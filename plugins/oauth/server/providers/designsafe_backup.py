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

from six.moves import urllib

from girder.api.rest import getApiUrl
from girder.exceptions import RestException
from girder.models.setting import Setting
from .base import ProviderBase
from .. import constants


class DesignSafe(ProviderBase):
    _AUTH_SCOPES = ['PRODUCTION']
    _AUTH_URL = 'https://agave.designsafe-ci.org/oauth2/authorize'
    _TOKEN_URL = 'https://agave.designsafe-ci.org/oauth2/token'
    _API_USER_URL = 'https://agave.designsafe-ci.org/profiles/v2/me'

    # tenants_url = "https://api.tacc.utexas.edu/tenants"
    # designsafe_base_url = "https://agave.designsafe-ci.org/"

    def getClientIdSetting(self):
        return Setting().get(constants.PluginSettings.DESIGNSAFE_CLIENT_ID)

    def getClientSecretSetting(self):
        return Setting().get(constants.PluginSettings.DESIGNSAFE_CLIENT_SECRET)

    @classmethod
    def getUrl(cls, state):
        # from pudb.remote import set_trace; set_trace(term_size=(160, 40), host='0.0.0.0', port=6900)
        clientId = Setting().get(constants.PluginSettings.DESIGNSAFE_CLIENT_ID)

        if clientId is None:
            raise Exception('No DesignSafe client ID setting is present.')

        callbackUrl = '/'.join((getApiUrl(), 'oauth', 'designsafe', 'callback'))

        query = urllib.parse.urlencode({
            'client_id': clientId,
            'redirect_uri': callbackUrl,
            'state': state,
            'scope': ','.join(cls._AUTH_SCOPES),
            'response_type': 'code'

        })
        return '%s?%s' % (cls._AUTH_URL, query)

    def getToken(self, code):
        # from pudb.remote import set_trace; set_trace(term_size=(160, 40), host='0.0.0.0', port=6900)
        params = {
            'code': code,
            'client_id': self.clientId,
            'client_secret': self.clientSecret,
            'redirect_uri': self.redirectUri,
            'grant_type': 'authorization_code'
        }
        # GitHub returns application/x-www-form-urlencoded unless
        # otherwise specified with Accept
        resp = self._getJson(method='POST', url=self._TOKEN_URL,
                             data=params,
                             headers={'Accept': 'application/json'})
        if 'error' in resp:
            raise RestException(
                'Got an error exchanging token from provider: "%s".' % resp,
                code=502)
        return resp

    def getUser(self, token):
        # from pudb.remote import set_trace; set_trace(term_size=(160, 40), host='0.0.0.0', port=6900)
        headers = {
            'Authorization': 'Bearer %s' % token['access_token'],
            'Accept': 'application/json'
        }

        # Get user's email address
        # In the unlikely case that a user has more than 30 email addresses,
        # this HTTP request might have to be made multiple times with pagination
        resp = self._getJson(method='GET', url=self._API_USER_URL, headers=headers)
        email = resp.get('result').get('email')

        if not email:
            raise RestException(
                'This DesignSafe user has no registered email address.', code=502)

        # Get user's OAuth2 ID, login, and name
        oauthId = resp.get('result').get('username')
        if not oauthId:
            raise RestException('DesignSafe did not return a user ID.', code=502)

        login = resp.get('result').get('username', '')
        firstName = resp.get('result').get('first_name')
        lastName = resp.get('result').get('last_name')

        return self._createOrReuseUser(oauthId, email, firstName, lastName, login)
