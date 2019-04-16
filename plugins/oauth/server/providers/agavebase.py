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
from .base import ProviderBase


class AgaveBase(ProviderBase):
    _AUTH_SCOPE = 'PRODUCTION'

    def getClientIdSetting(self):
        raise NotImplementedError()

    def getClientSecretSetting(self):
        raise NotImplementedError()

    @classmethod
    def getUrl(cls, state):
        # from pudb.remote import set_trace; set_trace(term_size=(160, 40), host='0.0.0.0', port=6900)
        clientId = cls.getClientId()

        if clientId is None:
            raise Exception('No ' + cls._NAME + ' client ID setting is present.')

        callbackUrl = '/'.join((getApiUrl(), 'oauth', cls._NAME.lower().replace(" ", ""), 'callback'))

        query = urllib.parse.urlencode({
            'client_id': clientId,
            'redirect_uri': callbackUrl,
            'state': state,
            'scope': cls._AUTH_SCOPE,
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

        resp = self._getJson(method='GET', url=self._API_USER_URL, headers=headers)
        email = resp.get('result').get('email')

        if not email:
            raise RestException(
                'This ' + self._NAME + ' user has no registered email address.', code=502)

        oauthId = resp.get('result').get('username')
        if not oauthId:
            raise RestException(self._NAME + ' did not return a user ID.', code=502)

        firstName = resp.get('result').get('first_name')
        lastName = resp.get('result').get('last_name')

        return self._createOrReuseUser(oauthId, email, firstName, lastName, oauthId)
