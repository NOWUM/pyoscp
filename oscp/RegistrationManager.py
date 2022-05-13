from multiprocessing import Lock
from dateutil import parser
import json
import secrets
import oscp.json_models as oj
import logging
from werkzeug.exceptions import Unauthorized, Forbidden, BadRequest
import requests
import threading
from flask import request
from datetime import datetime, timedelta
from packaging import version
from typing import List, Tuple

log = logging.getLogger('oscp')


# always communicate with latest version available
def _getLatestVersion(version_urls: List[str]) -> Tuple[str, str]:
    '''
    returns the latest semantic version and the base_url
    given a list of version_urls

    Parameters
    ----------
    version_urls : List[str]
        List of version_urls, dict-objects, containing version and url

    Returns
    -------
    Tuple(str,str)
        latest version and the related base_url

    '''

    latest = version.parse(version_urls[0]['version'])
    baseUrl = version_urls[0]['base_url']
    for v in version_urls:
        cur = version.parse(v['version'])
        if cur > latest:
            baseUrl = v['base_url']
            latest = cur
    return str(latest), baseUrl


def createOscpHeader(token: str, correlation: str = None):
    '''
    creates the http header to authenticate with the other participant

    token must be provided, optional correlation ID can be given,
    if the message refers to a previous message sent
    '''
    if not token:
        raise Exception('token must be provided')
    headers = {
        'Authorization': 'Token '+token,
        'X-Request-ID': secrets.token_urlsafe(8),
    }
    if correlation:
        headers['X-Correlation-ID'] = correlation
    return headers


class RegistrationMan(object):
    '''
    Base Registration manager independent of persistance technology
    '''

    def __init__(self, version_urls: list, background_interval: int = 5, **kwds):
        self.version_urls = version_urls
        # run background job every 5 seconds
        self.__stop_thread = False
        base_url, version = self._getSupportedVersion(
            [{
                "version": "2.0",
                "base_url": "http://127.0.0.1:5000/oscp/cp"
            }])

        super().__init__(**kwds)

        # and ['group_id1'] from dso1.json

        def bck_job():
            ticker = threading.Event()
            while not ticker.wait(background_interval):
                if self.__stop_thread:
                    break
                self._background_job()

        self.t = threading.Thread(
            target=bck_job, daemon=True, name='OSCP Worker')

    def start(self):
        log.info('starting oscp background job')
        self.t.start()

    def stop(self):
        log.info('stopping oscp background job')
        self.__stop_thread = True

    def _check_access_token(self):
        authHeader = request.headers.get("Authorization")
        if not authHeader:
            raise Unauthorized(description="Unauthorized")
        token = authHeader.replace('Token ', '').strip()
        if not self.isRegistered(token):
            raise Forbidden("invalid token")
        return token

    def handleRegister(self, payload: oj.Register):
        '''
        handles a registration message, if registered with tokenA
        saves the tokenB in the payload and answers with a generated tokenC
        as the response

        Further information in Section "2.6.1. Registration" of the OSCP 2.0
        standard.

        Parameters
        ----------
        payload : oj.Register
            the registration dict, containing the tokenB and the version_url

        Returns
        -------
        None.

        '''
        tokenA = self._check_access_token()
        # check if tokenA is authenticated, otherwise everybody can register
        req_id = request.headers.get("X-Request-ID")
        corr_id = request.headers.get("X-Correlation-ID")

        log.info('got register:' + str(payload))
        client_tokenB = payload['token']
        # - payload contains information to access client (tokenB)
        base_url, version = self._getSupportedVersion(payload['version_url'])
        self._updateService(
            tokenA, client_tokenB, base_url, version)

        if corr_id is None:
            tokenC = secrets.token_urlsafe(32)
            # remove tokenA, send new tokenC to enduser
            self._replaceToken(
                tokenA, tokenC, payload['token'], base_url, version)

            try:
                self._send_register(base_url, tokenC, client_tokenB, req_id)
            except requests.exceptions.ConnectionError:
                log.error(f"ConnError {base_url}")
            except requests.exceptions.HTTPError as e:
                log.error(f'{e.response.status_code} - {e.response.text}')
            except Exception:
                log.exception("error in register handling")
                # show token to enter in UI

    def updateEndpoint(self, payload: oj.Register):
        token = self._check_access_token()

        base_url, version = self._getSupportedVersion(payload['version_url'])
        log.info(f'update endpoint url for: {base_url}')
        self._updateService(token, payload['token'], base_url, version)

    def unregister(self):
        '''
        removes the token used to authenticate with this request
        '''
        token = self._check_access_token()
        log.info(f'unregistering {token}. Goodbye')
        self._removeService(token)

    def handleHandshake(self, payload: oj.Handshake):
        token = self._check_access_token()
        self._setRequiredBehavior(
            token, payload['required_behaviour'], new=True)
        log.info('handshake request for token ' + str(token))

    def handleHandshakeAck(self, payload: oj.HandshakeAcknowledgement):
        token = self._check_access_token()
        self._setRequiredBehavior(
            token, payload['required_behaviour'], new=False)
        log.info('handshake_ack received for token ' + str(token))

    def handleHeartbeat(self, payload: oj.Heartbeat):
        token = self._check_access_token()
        offline_at = datetime.strptime(
            payload['offline_mode_at'], "%Y-%m-%d %H:%M:%S")
        self._setOfflineAt(token, offline_at)
        log.info(
            f"got a heartbeat from {token}. Will be offline at: {offline_at}")

    def _getSupportedVersion(self, version_urls: List) -> Tuple[str, str]:
        for my_version in self.version_urls:
            for client_version in version_urls:
                if client_version['version'] == my_version['version']:
                    return client_version['base_url'], client_version['version']
        raise BadRequest('unsupported version')

    def _send_heartbeat(self, base_url: str, interval: int, token: str):
        '''
        sends a heartbeat to the given base_url
        '''
        next_heartbeat = datetime.now()+timedelta(seconds=interval)
        log.info(f'send heartbeat to {base_url}')
        offline_at = datetime.now()+3*timedelta(seconds=interval)
        data = {'offline_mode_at': offline_at.strftime(
            "%Y-%m-%d %H:%M:%S")}
        try:
            response = requests.post(
                base_url+'/heartbeat',
                headers=createOscpHeader(token),
                json=data)
            response.raise_for_status()
        except Exception:
            log.warning(f'sent heartbeat failed, URL: {base_url}')

        return next_heartbeat

    def _send_ack(self, base_url: str, interval: int, token: str):
        log.info(f'send ack for {base_url}')
        # send ack for new handshakes

        data = {}  # not interested in heartbeats
        data = {'required_behaviour': {
            'heartbeat_interval': interval}}
        response = requests.post(
            base_url+'/handshake_acknowledgment',
            headers=createOscpHeader(token),
            json=data)
        response.raise_for_status()

    def _send_register(self, base_url: str, new_token: str, client_token: str, correlation: str = None):
        url = base_url + '/register'
        log.debug(f"send register to {url} with auth: {client_token}")

        data = {'token': new_token,
                'version_url': self.version_urls}

        response = requests.post(url,
                                 headers=createOscpHeader(client_token, correlation),
                                 json=data)
        response.raise_for_status()

    def _background_job(self):
        log.debug('run backgroundjob')

        # for all endpoints
        # if endpoint has handshaked
        #     self._send_ack(base_url, interval, token)
        # if endpoint heartbeat is due -> send heartbeat
        #     next_beat = self._send_heartbeat(base_url, interval, token)

        # if time since last heartbeat is long ago -> set offline

        # send register for new tokens (whatever new means)
        #     self._send_register(base_url, new_token, client_token)

    def getURL(self, token: str = None, group_id: str = None):
        '''
        returns the Client URL and the related Token to access the client
        using the given token to access this api

        returns none if token could not be found
        '''
        url = None
        client_token = None
        if token == None:
            log.error('Token argument must be given.')

        if token:
            try:
                url, client_token = self._url_by_token(token)
                log.debug(f'URL: {url}')
            except KeyError:
                log.error(f'Invalid token: {token}')
        return url, client_token

    def getEndpoints(self):
        raise NotImplementedError()

    def isRegistered(self, token):
        raise NotImplementedError()

    def _updateService(self, token, client_token=None, client_url=None, version=None):
        raise NotImplementedError()

    def _setGroupIds(self, token, group_ids):
        raise NotImplementedError()

    def _setRequiredBehavior(self, token: str, req_behavior: dict, new=True):
        raise NotImplementedError()

    def _removeService(self, token: str):
        raise NotImplementedError()

    def _replaceToken(self, token_old, token_new, client_token, client_url, version):
        self._removeService(token_old)
        self._updateService(token_new, client_token, client_url, version)

    def _isAuthorized(self, token: str):
        raise NotImplementedError()

    def _setOfflineAt(self, token: str, offline_at: datetime):
        raise NotImplementedError()

    def _token_by_group_id(self, group_id: str):
        raise NotImplementedError()

    def _url_by_token(self, token: str) -> Tuple[str, str]:
        raise NotImplementedError()


def StoD(string: str):
    return parser.parse(string)


def DtoS(date):
    return date.isoformat()


lock = Lock()


class RegistrationDictMan(RegistrationMan):
    def __init__(self, version_urls, filename='./endpoints.json'):
        self.filename = filename

        self.writeJson({})
        super().__init__(version_urls)

    def readJson(self):
        with open(self.filename, 'r') as f:
            return json.load(f)

    def writeJson(self, endpoints):
        with open(self.filename, 'w') as f:
            json.dump(endpoints, f, indent=4, sort_keys=False)

    def _updateService(self, token, client_token=None, client_url=None, version=None):
        with lock:
            endpoints = self.readJson()
            data = {'register':
                    {'token': client_token,
                     'base_url': client_url}
                    }
            if endpoints.get(token):
                # updates client_token and version_url without touching other stuff
                endpoints[token].update(data)
            else:
                endpoints[token] = data
            self.writeJson(endpoints)

    def _setGroupIds(self, token, group_ids):
        with lock:
            endpoints = self.readJson()
            endpoints[token].update({"group_ids": group_ids})
            self.writeJson(endpoints)

    def _setRequiredBehavior(self, token, required_behavior, new=True):
        with lock:
            endpoints = self.readJson()
            endpoints[token]['new'] = new
            endpoints[token]['required_behavior'] = required_behavior
            self.writeJson(endpoints)

    def _removeService(self, token):
        with lock:
            endpoints = self.readJson()
            endpoints.pop(token)
            self.writeJson(endpoints)

    def getEndpoints(self):
        return self.readJson()

    def isRegistered(self, token):
        with lock:
            endpoints = self.readJson()
        return token in endpoints

    def _setOfflineAt(self, token, offline_at):
        with lock:
            endpoints = self.readJson()
            endpoints[token]['offline_at'] = DtoS(offline_at)
            self.writeJson(endpoints)

    def _token_by_group_id(self, group_id):
        token = None
        endpoints = self.readJson()
        for t, v in endpoints.items():
            if group_id in v['group_ids']:
                log.debug(f'Found token: {t} for group_id: {group_id}')
                token = t
        if token == None:
            log.error(f'No token found for group_id: {group_id}')
        return token

    def _url_by_token(self, token) -> Tuple[str, str]:
        endpoints = self.readJson()
        base_url = endpoints[token]['register']['base_url']
        token = endpoints[token]['register']['token']
        return base_url, token

    def _background_job(self):
        with lock:
            endpoints = self.readJson()
            for endpoint_token, endpoint in endpoints.items():
                try:
                    base_url = endpoint['register']['base_url']
                    if endpoint.get('new') == True:
                        # send ack for new handshakes

                        interval = endpoint['required_behavior']['heartbeat_interval']
                        token = endpoint['register']['token']
                        try:
                            self._send_ack(base_url, interval, token)
                            endpoint['new'] = False
                        except requests.exceptions.ConnectionError:
                            log.error(f'Connection failed: {base_url}')

                    if endpoint.get('required_behavior') != None:
                        nb = endpoint.get('next_heartbeat')
                        if nb is None or (StoD(nb) < datetime.now()):
                            # next heartbeat is due, send it

                            interval = endpoint['required_behavior']['heartbeat_interval']
                            token = endpoint['register']['token']
                            endpoint['next_heartbeat'] = DtoS(self._send_heartbeat(
                                base_url, interval, token))

                    if endpoint.get('should_register') == True:
                        client_token = endpoint['register']['token']
                        try:
                            self._send_register(
                                base_url, endpoint_token, client_token)
                            endpoint['should_register'] = False
                            endpoint['new'] = True
                        except requests.exceptions.ConnectionError:
                            log.error(f'Connection failed: {base_url}')
                        except Exception as e:
                            log.exception(e)

                    offline_at = endpoint.get('offline_at')
                    if offline_at != None and StoD(offline_at) < datetime.now():
                        log.warning(
                            f'{base_url} endpoint is offline. No Heartbeat received before {offline_at}')
                except Exception:
                    log.exception(f'OSCP background job failed for {base_url}')
            self.writeJson(endpoints)
