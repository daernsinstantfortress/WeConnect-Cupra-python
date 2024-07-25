from enum import Enum, auto
import time
import logging
from oauthlib.oauth2.rfc6749.errors import InsecureTransportError, TokenExpiredError
from oauthlib.oauth2.rfc6749.utils import is_secure_transport

import requests

from oauthlib.common import UNICODE_ASCII_CHARACTER_SET, generate_nonce, generate_token
from oauthlib.oauth2.rfc6749.parameters import parse_authorization_code_response, parse_token_response, prepare_grant_uri

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from weconnect_cupra.auth.auth_util import addBearerAuthHeader
from weconnect_cupra.errors import AuthentificationError, RetrievalError


LOG = logging.getLogger("weconnect_cupra")


class AccessType(Enum):
    NONE = auto()
    ACCESS = auto()
    ID = auto()
    REFRESH = auto()


class OpenIDSession(requests.Session):
    def __init__(self, client_id=None, redirect_uri=None, refresh_url=None, scope=None, token=None, state=None, timeout=None, **kwargs):
        super(OpenIDSession, self).__init__(**kwargs)
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.refresh_url = refresh_url
        self.scope = scope
        self.state = state or generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET)

        self.timeout = timeout
        self._token = None
        self.token = token

        self._retries = False

    @property
    def retries(self):
        return self._retries

    @retries.setter
    def retries(self, newValue):
        self._retries = newValue
        if newValue:
            # Retry on internal server error (500)
            retries = Retry(total=newValue,
                            backoff_factor=2,
                            status_forcelist=[500],
                            raise_on_status=False)
            self.mount('https://', HTTPAdapter(max_retries=retries))

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, newToken):
        if newToken is not None:
            # If new token e.g. after refresh is missing expires_in we assume it is the same than before
            if 'expires_in' not in newToken:
                if self._token is not None and 'expires_in' in self._token:
                    newToken['expires_in'] = self._token['expires_in']
                else:
                    newToken['expires_in'] = 3600
            # It expires_in is set and expires_at is not set we calculate expires_at from expires_in using the current time
            if 'expires_in' in newToken and 'expires_at' not in newToken:
                newToken['expires_at'] = time.time() + int(newToken.get('expires_in'))
        self._token = newToken

    @property
    def accessToken(self):
        if self._token is not None and 'access_token' in self._token:
            return self._token.get('access_token')
        return None

    @accessToken.setter
    def accessToken(self, newValue):
        if self._token is None:
            self._token = {}
        self._token['access_token'] = newValue

    @property
    def refreshToken(self):
        if self._token is not None and 'refresh_token' in self._token:
            return self._token.get('refresh_token')
        return None

    @property
    def idToken(self):
        if self._token is not None and 'id_token' in self._token:
            return self._token.get('id_token')
        return None

    @property
    def tokenType(self):
        if self._token is not None and 'token_type' in self._token:
            return self._token.get('token_type')
        return None

    @property
    def expiresIn(self):
        if self._token is not None and 'expires_in' in self._token:
            return self._token.get('expires_in')
        return None

    @property
    def expiresAt(self):
        if self._token is not None and 'expires_at' in self._token:
            return self._token.get('expires_at')
        return None

    @property
    def authorized(self):
        return bool(self.accessToken)

    @property
    def expired(self):
        return self.expiresAt is not None and self.expiresAt < time.time()

    def login(self):
        pass

    def refresh(self):
        pass

    def authorizationUrl(self, url, state=None, **kwargs):
        state = state or self.state
        authUrl = prepare_grant_uri(uri=url, client_id=self.client_id, redirect_uri=self.redirect_uri, response_type='code id_token token', scope=self.scope,
                                    state=state, nonce=generate_nonce(), **kwargs)
        return authUrl

    def parseFromFragment(self, authorization_response, state=None):
        state = state or self.state
        self.token = parse_authorization_code_response(authorization_response, state=state)
        return self.token

    def parseFromBody(self, token_response, state=None):
        self.token = parse_token_response(token_response, scope=self.scope)
        return self.token

    def request(
        self,
        method,
        url,
        data=None,
        headers=None,
        withhold_token=False,
        access_type=AccessType.ACCESS,
        token=None,
        timeout=None,
        **kwargs
    ):
        """Intercept all requests and add the OAuth 2 token if present."""
        if not is_secure_transport(url):
            raise InsecureTransportError()
        if access_type != AccessType.NONE and not withhold_token:
            try:
                url, headers, data = self.addToken(url, body=data, headers=headers, access_type=access_type, token=token)
            # Attempt to retrieve and save new access token if expired
            except TokenExpiredError:
                LOG.info('Token expired')
                self.accessToken = None
                try:
                    self.refresh()
                except AuthentificationError:
                    self.login()
                except RetrievalError:
                    raise
                url, headers, data = self.addToken(url, body=data, headers=headers, access_type=access_type, token=token)

        if timeout is None:
            timeout = self.timeout

        return super(OpenIDSession, self).request(
            method, url, headers=headers, data=data, timeout=timeout, **kwargs
        )

    def addToken(self, uri, body=None, headers=None, access_type=AccessType.ACCESS, token=None, **kwargs):
        if not is_secure_transport(uri):
            raise InsecureTransportError()

        if token is None:
            if access_type == AccessType.ID:
                if not (self.idToken):
                    raise ValueError("Missing id token.")
                token = self.idToken
            elif access_type == AccessType.REFRESH:
                if not (self.refreshToken):
                    raise ValueError("Missing refresh token.")
                token = self.refreshToken
            else:
                if not self.authorized:
                    self.login()
                if not (self.accessToken):
                    raise ValueError("Missing access token.")
                if self.expired:
                    raise TokenExpiredError()
                token = self.accessToken

        headers = addBearerAuthHeader(token, headers)

        return (uri, headers, body)
