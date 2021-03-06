#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
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

from girder.models.setting import Setting
from .agavebase import AgaveBase
from .. import constants


class CyVerse(AgaveBase):
    _AUTH_URL = 'https://agave.iplantc.org/oauth2/authorize'
    _TOKEN_URL = 'https://agave.iplantc.org/oauth2/token'
    _API_USER_URL = 'https://agave.iplantc.org/profiles/v2/me'
    _NAME = 'CyVerse'

    @staticmethod
    def getClientId():
        return Setting().get(constants.PluginSettings.CYVERSE_CLIENT_ID)

    def getClientIdSetting(self):
        return Setting().get(constants.PluginSettings.CYVERSE_CLIENT_ID)

    def getClientSecretSetting(self):
        return Setting().get(constants.PluginSettings.CYVERSE_CLIENT_SECRET)
