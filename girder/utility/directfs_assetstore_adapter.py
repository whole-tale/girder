#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2013 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import os
import pathlib
import filelock
import stat
import shutil

from girder import logger
from girder.models.upload import Upload
from girder.models.item import Item
from girder.models.folder import Folder
from girder.utility import mkdir
from girder.utility import path as path_lib
from . import hash_state
from .filesystem_assetstore_adapter import FilesystemAssetstoreAdapter

BUF_SIZE = 65536

# Default permissions for the files written to the filesystem
DEFAULT_PERMS = stat.S_IRUSR | stat.S_IWUSR


class DirectFSAssetstoreAdapter(FilesystemAssetstoreAdapter):
    """
    This assetstore type stores files on the filesystem underneath a root
    directory.

    :param assetstore: The assetstore to act on.
    :type assetstore: dict
    """

    def finalizeUpload(self, upload, file):
        """
        Moves the file into its permanent content-addressed location within the
        assetstore. Directory hierarchy yields 256^2 buckets.
        """
        hash = hash_state.restoreHex(
            upload['sha512state'], 'sha512').hexdigest()

        if upload['parentType'] == 'folder':
            parent = Folder().load(id=upload['parentId'], force=True)
        else:
            parent = Item().load(id=upload['parentId'], force=True)
        fullPath = path_lib.getResourcePath(upload['parentType'], parent,
                                            force=True)
        fullPath = pathlib.Path(os.path.join(fullPath, upload['name']))
        path = '{}/{}'.format(
            fullPath.parts[2], os.sep.join(fullPath.parts[4:])).rstrip(os.sep)
        abspath = os.path.join(self.assetstore['root'], path)
        absdir = os.path.dirname(abspath)

        # Store the hash in the upload so that deleting a file won't delete
        # this file
        if '_id' in upload:
            upload['sha512'] = hash
            Upload().update(
                {'_id': upload['_id']}, update={'$set': {'sha512': hash}})

        mkdir(absdir)

        # Only maintain the lock which checking if the file exists.  The only
        # other place the lock is used is checking if an upload task has
        # reserved the file, so this is sufficient.
        with filelock.FileLock(abspath + '.deleteLock'):
            pathExists = os.path.exists(abspath)
        if pathExists:
            # Already have this file stored, just delete temp file.
            os.unlink(upload['tempFile'])
        else:
            # Move the temp file to permanent location in the assetstore.
            # shutil.move works across filesystems
            shutil.move(upload['tempFile'], abspath)
            try:
                os.chmod(abspath, self.assetstore.get('perms', DEFAULT_PERMS))
            except OSError:
                # some filesystems may not support POSIX permissions
                pass

        file['sha512'] = hash
        file['path'] = path

        return file

    def deleteFile(self, file):
        if file.get('imported') or 'path' not in file:
            return
        if os.path.isfile(file['path']):
            try:
                os.unlink(file['path'])
            except Exception:
                logger.exception('Failed to delete file %s' % file['path'])
