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

import functools
import six

from girder.api import rest
from girder.models.model_base import AccessException
from girder.utility.model_importer import ModelImporter

_tokenModel = ModelImporter.model('token')


def admin(*args, **kwargs):
    """
    Functions that require administrator access should be wrapped in this
    decorator.

    :param scope: To also expose this endpoint for certain token scopes,
        pass those scopes here. If multiple are passed, all will be required.
    :type scope: str or list of str
    """
    if len(args) == 1 and callable(args[0]):  # Raw decorator
        @six.wraps(args[0])
        def wrapped(*iargs, **ikwargs):
            rest.requireAdmin(rest.getCurrentUser())
            return args[0](*iargs, **ikwargs)
        wrapped.accessLevel = 'admin'
        return wrapped
    else:  # We should return a decorator
        def dec(fun):
            @six.wraps(fun)
            def wrapped(*iargs, **ikwargs):
                token = rest.getCurrentToken()
                if not _tokenModel.hasScope(token, kwargs.get('scope')):
                    rest.requireAdmin(rest.getCurrentUser())
                return fun(*iargs, **ikwargs)
            wrapped.accessLevel = 'admin'
            return wrapped
        return dec


def user(*args, **kwargs):
    """
    Functions that require a logged-in user should be wrapped with this access
    decorator.

    :param scope: To also expose this endpoint for certain token scopes,
        pass those scopes here. If multiple are passed, all will be required.
    :type scope: str or list of str
    """
    if len(args) == 1 and callable(args[0]):  # Raw decorator
        @six.wraps(args[0])
        def wrapped(*iargs, **ikwargs):
            if not rest.getCurrentUser():
                raise AccessException('You must be logged in.')
            return args[0](*iargs, **ikwargs)
        wrapped.accessLevel = 'user'
        return wrapped
    else:  # We should return a decorator
        def dec(fun):
            @six.wraps(fun)
            def wrapped(*iargs, **ikwargs):
                token = rest.getCurrentToken()
                if (not _tokenModel.hasScope(token, kwargs.get('scope')) and
                        not rest.getCurrentUser()):
                    raise AccessException('You must be logged in.')
                return fun(*iargs, **ikwargs)
            wrapped.accessLevel = 'user'
            return wrapped
        return dec


def token(*args, **kwargs):
    """
    Functions that require a token, but not necessarily a user authentication
    token, should use this access decorator.

    :param scope: The scope or list of scopes required for this token.
    :type scope: str or list of str
    """
    if len(args) == 1 and callable(args[0]):  # Raw decorator
        @six.wraps(args[0])
        def wrapped(*iargs, **ikwargs):
            if not rest.getCurrentToken():
                raise AccessException(
                    'You must be logged in or have a valid auth token.')
            return args[0](*iargs, **ikwargs)
        wrapped.accessLevel = 'token'
        return wrapped
    else:  # We should return a decorator
        def dec(fun):
            @six.wraps(fun)
            def wrapped(*iargs, **ikwargs):
                token = rest.getCurrentToken()
                if not _tokenModel.hasScope(token, kwargs.get('scope')):
                    raise AccessException(
                        'You must be logged in or have a valid auth token.')
                return fun(*iargs, **ikwargs)
            wrapped.accessLevel = 'token'
            return wrapped
        return dec


def public(fun):
    """
    Functions that allow any client access, including those that haven't logged
    in should be wrapped in this decorator.
    """
    @functools.wraps(fun)
    def accessDecorator(*args, **kwargs):
        return fun(*args, **kwargs)
    accessDecorator.accessLevel = 'public'
    return accessDecorator
