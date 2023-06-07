from __future__ import annotations
from typing import Dict, List, Set, Tuple, Callable, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import os

import requests

from weconnect_cupra.auth.openid_session import OpenIDSession
from weconnect_cupra.weconnect_errors import ErrorEventType
from weconnect_cupra.errors import ErrorBus, RetrievalError
from weconnect_cupra.util import ExtendedEncoder


LOG = logging.getLogger("weconnect_cupra")


class Fetcher:

    def __init__(self,
        session: OpenIDSession,
        errorBus: ErrorBus,
        maxAge: Optional[int] = None,
        maxAgePictures: Optional[int] = None,
    ):
        self.__cache: Dict[str, Any] = {}
        self.maxAge: Optional[int] = maxAge
        self.maxAgePictures: Optional[int] = maxAgePictures
        self.session = session
        self.__elapsed: List[timedelta] = []
        self.__errorBus: ErrorBus = errorBus
        self.__base_url: str = 'https://localhost'

    def recordElapsed(self, elapsed: timedelta) -> None:
        self.__elapsed.append(elapsed)

    def fetchData(self, url, force=False, allowEmpty=False, allowHttpError=False, allowedErrors=None) -> Optional[Dict[str, Any]]:  # noqa: C901
        data: Optional[Dict[str, Any]] = None
        cacheDate: Optional[datetime] = None
        if not force and (self.maxAge is not None and self.cache is not None and url in self.cache):
            data, cacheDateString = self.cache[url]
            cacheDate = datetime.fromisoformat(cacheDateString)
        if data is None or self.maxAge is None \
                or (cacheDate is not None and cacheDate < (datetime.utcnow() - timedelta(seconds=self.maxAge))):
            try:
                statusResponse: requests.Response = self.session.get(url, allow_redirects=False)
                self.recordElapsed(statusResponse.elapsed)
                if statusResponse.status_code in (requests.codes['ok'], requests.codes['multiple_status']):

                    data = statusResponse.json()
                    if self.cache is not None:
                        self.cache[url] = (data, str(datetime.utcnow()))

                elif statusResponse.status_code == requests.codes['unauthorized']:

                    LOG.info('Server asks for new authorization')
                    self.session.login()
                    statusResponse = self.session.get(url, allow_redirects=False)
                    self.recordElapsed(statusResponse.elapsed)

                    if statusResponse.status_code in (requests.codes['ok'], requests.codes['multiple_status']):
                        data = statusResponse.json()
                        if self.cache is not None:
                            self.cache[url] = (data, str(datetime.utcnow()))
                    elif not allowHttpError or (allowedErrors is not None and statusResponse.status_code not in allowedErrors):
                        
                        self.__errorBus.notifyError(self, ErrorEventType.HTTP, str(statusResponse.status_code), 'Could not fetch data due to server error')
                        raise RetrievalError(f'Could not fetch data even after re-authorization. Status Code was: {statusResponse.status_code}')

                elif not allowHttpError or (allowedErrors is not None and statusResponse.status_code not in allowedErrors):

                    self.__errorBus.notifyError(self, ErrorEventType.HTTP, str(statusResponse.status_code), 'Could not fetch data due to server error')
                    raise RetrievalError(f'Could not fetch data. Status Code was: {statusResponse.status_code}')

            except requests.exceptions.ConnectionError as connectionError:

                self.__errorBus.notifyError(self, ErrorEventType.CONNECTION, 'connection', 'Could not fetch data due to connection problem')
                raise RetrievalError from connectionError

            except requests.exceptions.ChunkedEncodingError as chunkedEncodingError:

                self.__errorBus.notifyError(self, ErrorEventType.CONNECTION, 'chunked encoding error',
                                 'Could not fetch data due to connection problem with chunked encoding')
                raise RetrievalError from chunkedEncodingError

            except requests.exceptions.ReadTimeout as timeoutError:

                self.__errorBus.notifyError(self, ErrorEventType.TIMEOUT, 'timeout', 'Could not fetch data due to timeout')
                raise RetrievalError from timeoutError

            except requests.exceptions.RetryError as retryError:

                raise RetrievalError from retryError

            except requests.exceptions.JSONDecodeError as jsonError:

                if allowEmpty:
                    data = None
                else:
                    self.__errorBus.notifyError(self, ErrorEventType.JSON, 'json', 'Could not fetch data due to error in returned data')
                    raise RetrievalError from jsonError
        
        self.__cache[url] = (data, str(datetime.utcnow()))

        LOG.debug(f'Retrieved data from url: {url}')
        LOG.debug(json.dumps(data))

        return data

    def post(self, url, data=None, allow_redirects=True, headers={}):
        return self.session.post(url=url, data=data, allow_redirects=allow_redirects, headers=headers)

    def put(self, url, data=None, json=None, allow_redirects=True, headers={}):
        return self.session.put(url=url, data=data, json=json, allow_redirects=allow_redirects, headers=headers)

    @property
    def user_id(self):
        # TODO better typing so we don't have to ignore here
        return self.session.user_id  # type: ignore

    @property
    def base_url(self):
        return self.__base_url

    @base_url.setter
    def base_url(self, value):
        self.__base_url = value

    @property
    def cache(self) -> Dict[str, Any]:
        return self.__cache

    @property
    def errors(self): 
        return self.__errorBus

    def persistCacheAsJson(self, filename: str) -> None:
        with open(filename, 'w', encoding='utf8') as file:
            json.dump(self.__cache, file, cls=ExtendedEncoder)
        LOG.info('Writing cachefile %s', filename)

    def fillCacheFromJson(self, filename: str, maxAge: int, maxAgePictures: Optional[int] = None) -> None:
        self.maxAge = maxAge
        if maxAgePictures is None:
            self.maxAgePictures = maxAge
        else:
            self.maxAgePictures = maxAgePictures

        try:
            with open(filename, 'r', encoding='utf8') as file:
                self.__cache = json.load(file)
        except json.decoder.JSONDecodeError:
            LOG.error('Cachefile %s seems corrupted will delete it and try to create a new one. '
                      'If this problem persists please check if a problem with your disk exists.', filename)
            os.remove(filename)
        LOG.info('Reading cachefile %s', filename)

    def fillCacheFromJsonString(self, jsonString, maxAge: int, maxAgePictures: Optional[int] = None) -> None:
        self.maxAge = maxAge
        if maxAgePictures is None:
            self.maxAgePictures = maxAge
        else:
            self.maxAgePictures = maxAgePictures

        self.__cache = json.loads(jsonString)
        LOG.info('Reading cache from string')

    def clearCache(self) -> None:
        self.__cache.clear()
        LOG.info('Clearing cache')
