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

log = logging.getLogger('oscp')


# always communicate with latest version available
def _getLatestVersion(version_urls):
    latest = version.parse(version_urls[0]['version'])
    baseUrl = version_urls[0]['base_url']
    for v in version_urls:
        cur = version.parse(v['version'])
        if cur > latest:
            baseUrl = v['base_url']
            latest = cur
    return str(latest), baseUrl


def createOscpHeader(token: str, correlation=None):
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

    def __init__(self, version_urls: list, background_interval=5):
        self.version_urls = version_urls
        # run background job every 5 seconds
        self.__stop_thread = False
        base_url, version = self._getSupportedVersion(
            [{
                "version": "2.0",
                "base_url": "http://127.0.0.1:5000/oscp/cp"
            }])

        # and ['group_id1'] from dso1.json

        def bck_job():
            ticker = threading.Event()
            while not ticker.wait(background_interval):
                if self.__stop_thread:
                    break
                self._background_job()

        self.t = threading.Thread(target=bck_job, daemon=True)

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
            self._removeService(tokenA)
            # remove tokenA, send new tokenC to enduser
            tokenC = secrets.token_urlsafe(32)
            data = {'token': tokenC, 'version_url': self.version_urls}

            self._addService(
                tokenC, payload['token'], base_url, version)
            try:
                response = requests.post(
                    base_url+'/register',
                    json=data,
                    headers=createOscpHeader(client_tokenB, req_id))
                log.info(
                    f"send register to {base_url + '/register'} with auth: {client_tokenB}")
                if response.status_code >= 205:
                    raise Exception(f'{response.status_code}, {response.json()}')
            except requests.exceptions.ConnectionError:
                log.error("connection failed")
            except Exception:
                log.exception("error in register handling")
                log.warning(tokenC)
                # show token to enter in UI

    def updateEndpoint(self, payload: oj.Register):
        token = self._check_access_token()

        base_url, version = self._getSupportedVersion(payload['version_url'])
        log.info(f'update endpoint url for: {base_url}')
        self._addService(token, payload['token'], base_url, version)

    def unregister(self):
        token = self._check_access_token()
        log.info('unregistering ' + str(token) + '. Goodbye')
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
        log.info(f"got a heartbeat from {token}. Will be offline at: {offline_at}")

    def _getSupportedVersion(self, version_urls):
        for my_version in self.version_urls:
            for client_version in version_urls:
                if client_version['version'] == my_version['version']:
                    return client_version['base_url'], client_version['version']
        raise BadRequest('unsupported version')

    def _send_heartbeat(self, base_url, interval, token):
        next_heartbeat = datetime.now()+timedelta(seconds=interval)
        log.info('send heartbeat to '+base_url)
        offline_at = datetime.now()+3*timedelta(seconds=interval)
        data = {'offline_mode_at': offline_at.strftime(
            "%Y-%m-%d %H:%M:%S")}
        try:
            response = requests.post(
                base_url+'/heartbeat',
                headers=createOscpHeader(token),
                json=data)
            if response.status_code >= 205:
                raise Exception(response.text)
        except:
            log.info('sent heartbeat failed: '+base_url)

        return next_heartbeat

    def _send_ack(self, base_url, interval, token):
        log.info(f'send ack for {base_url}')
        # send ack for new handshakes

        data = {}  # not interested in heartbeats
        data = {'required_behaviour': {
            'heartbeat_interval': interval}}
        response = requests.post(
            base_url+'/handshake_acknowledgment',
            headers=createOscpHeader(token),
            json=data)
        if response.status_code >= 205:
            raise Exception(response.text)

    def _send_register(self, base_url, new_token, client_token):
        log.info('send register to '+base_url)

        data = {'token': new_token,
                'version_url': self.version_urls}

        response = requests.post(
            base_url+'/register',
            headers=createOscpHeader(client_token),
            json=data)
        if response.status_code >= 205:
            raise Exception(response.text)

    def _background_job(self):
        log.debug('run backgroundjob')

        # for all endpoints
        # if endpoint has handshaked
        #     self._send_ack(base_url, interval, token)
        # if endpoint heartbeat is due -> send heartbeat
        #     self._send_heartbeat(base_url, interval, token)

        # if time since last heartbeat is long ago -> set offline

        # send register for new tokens (whatever new means)
        #     self._send_register(base_url, new_token, client_token)

    def getURL(self, token=None, group_id=None):
        '''
        returns the Client URL and the related Token to access the client
        using the given token to access this api

        returns none if token could not be found
        '''
        url = None
        client_token = None
        if token == None and group_id == None:
            log.error('Either token or group_id must be given.')
        elif token == None and group_id:
            try:
                token = self._token_by_group_id(group_id)
            except KeyError:
                log.error(f'invalid group_id: {group_id}')

        if token:
            try:
                url, client_token = self._url_by_token(token)
            except KeyError:
                log.error(f'invalid token: {token}')

        log.debug(f'URL: {url}')
        return url, client_token

    def getEndpoints(self):
        raise NotImplementedError()

    def isRegistered(self, token):
        raise NotImplementedError()

    def _addService(self, token, client_token, client_url, version=None):
        raise NotImplementedError()

    def _updateService(self, token, client_token=None, client_url=None, version=None):
        raise NotImplementedError()

    def _setGroupIds(self, token, group_ids):
        raise NotImplementedError()

    def getGroupIds(self, token):
        raise NotImplementedError()

    def _setRequiredBehavior(self, token, req_behavior, new=True):
        raise NotImplementedError()

    def _removeService(self, token):
        raise NotImplementedError()

    def _isAuthorized(self, token):
        raise NotImplementedError()

    def _setOfflineAt(self, token, offline_at):
        raise NotImplementedError()

    def _token_by_group_id(self, group_id):
        raise NotImplementedError()

    def _url_by_token(self, token):
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

    def _addService(self, token, client_token, client_url, version=None):
        with lock:
            endpoints = self.readJson()
            endpoints[token] = {'register':
                                {'token': client_token,
                                 'base_url': client_url}
                                }
            log.debug(f'endpoints: {endpoints}')
            self.writeJson(endpoints)

    def _updateService(self, token, client_token=None, client_url=None, version=None):
        with lock:
            endpoints = self.readJson()
            data = {'register':
                    {'token': client_token,
                     'base_url': client_url}
                    }
            # updates client_token and version_url without touching other stuff
            endpoints[token].update(data)
            self.writeJson(endpoints)

    def _setGroupIds(self, token, group_ids):
        with lock:
            endpoints = self.readJson()
            endpoints[token].update({"group_ids": group_ids})
            self.writeJson(endpoints)

    def getGroupIds(self, token):
        endpoints = self.readJson()
        return endpoints[token].get("group_ids")

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

    def _url_by_token(self, token):
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
                            self._send_register(base_url, endpoint_token, client_token)
                            endpoint['should_register'] = False
                            endpoint['new'] = True
                        except requests.exceptions.ConnectionError:
                            log.error(f'Connection failed: {base_url}')
                        except Exception as e:
                            log.exception(e)

                    offline_at = endpoint.get('offline_at')
                    if offline_at != None and StoD(offline_at) < datetime.now():
                        log.info(
                            f'{base_url} endpoint is offline. No Heartbeat received before {offline_at}')
                except Exception:
                    log.exception(f'OSCP background job failed for {base_url}')
            self.writeJson(endpoints)