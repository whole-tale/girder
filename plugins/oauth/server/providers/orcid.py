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

import requests
from six.moves import urllib

from girder.api.rest import getApiUrl
from girder.exceptions import RestException
from girder.models.setting import Setting
from .base import ProviderBase
from .. import constants


class ORCID(ProviderBase):
    _AUTH_URL = "https://orcid.org/oauth/authorize"
    _AUTH_SCOPES = ["/authenticate"]
    _TOKEN_URL = "https://orcid.org/oauth/token"
    _REVOKE_URL = "https://orcid.org/oauth/revoke"
    _API_USER_URL = "https://pub.orcid.org/v2.0/{orcid}/person"

    # header for user: application/vnd.orcid+json

    def getClientIdSetting(self):
        return Setting().get(constants.PluginSettings.ORCID_CLIENT_ID)

    def getClientSecretSetting(self):
        return Setting().get(constants.PluginSettings.ORCID_CLIENT_SECRET)

    @classmethod
    def getUrl(cls, state):
        clientId = Setting().get(constants.PluginSettings.ORCID_CLIENT_ID)

        if clientId is None:
            raise Exception("No ORCID client ID setting is present.")

        callbackUrl = "/".join((getApiUrl(), "oauth", "orcid", "callback"))

        query = urllib.parse.urlencode(
            {
                "client_id": clientId,
                "response_type": "code",
                "redirect_uri": callbackUrl,
                "state": state,
                "scope": ",".join(cls._AUTH_SCOPES),
            }
        )
        return "%s?%s" % (cls._AUTH_URL, query)

    def getToken(self, code):
        params = {
            "code": code,
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
            "redirect_uri": self.redirectUri,
            "grant_type": "authorization_code",
        }
        resp = self._getJson(
            method="POST",
            url=self._TOKEN_URL,
            data=params,
            headers={"Accept": "application/json"},
        )
        if "error" in resp:
            raise RestException(
                'Got an error exchanging token from provider: "%s".' % resp, code=502
            )
        return resp

    def revokeToken(self, token):
        params = {
            "token": token["refresh_token"],
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
        }

        resp = requests.request(
            method="POST",
            url=self._REVOKE_URL,
            data=params,
            headers={"Accept": "application/json"},
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            raise RestException(
                'Got %s code from provider, response="%s".'
                % (resp.status_code, resp.content.decode("utf8")),
                code=502,
            )

    def refreshToken(self, token):
        params = {
            "refresh_token": token["refresh_token"],
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
            "grant_type": "refresh_token",
        }
        resp = self._getJson(
            method="POST",
            url=self._TOKEN_URL,
            data=params,
            headers={"Accept": "application/json"},
        )
        if "error" in resp:
            raise RestException(
                'Got an error refreshing token from provider: "%s".' % resp, code=502
            )
        return resp

    def getUser(self, token):
        headers = {
            "Authorization": "Bearer %s" % token["access_token"],
            "Accept": "application/vnd.orcid+json",
        }

        # Get user's email address
        resp = self._getJson(
            method="GET", url=self._API_USER_URL.format(**token), headers=headers
        )

        try:
            email = resp["emails"]["email"][0]
        except (KeyError, TypeError, IndexError):
            email = "{orcid}@orcid.org".format(**token)

        oauthId = token["orcid"]
        if not oauthId:
            raise RestException("ORCID did not return a user ID.", code=502)

        login = ""
        lastName = resp["name"]["family-name"]["value"]
        firstName = resp["name"]["given-names"]["value"]

        return self._createOrReuseUser(oauthId, email, firstName, lastName, login)
