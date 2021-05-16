import secrets
import requests as r
import oscp.json_models as oj
import logging
from werkzeug.exceptions import Unauthorized, Forbidden
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


class RegistrationMan(object):
    '''
    Base Registration manager independent of persistance technology
    '''

    def __init__(self, version_urls: list, background_interval=5):
        self.version_urls = version_urls
        # run background job every 5 seconds
        self.__stop_thread = False

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
        token = request.headers.get("Authorization")
        if not token:
            raise Unauthorized(description="Unauthorized")

        if not self.isRegistered(token):
            raise Forbidden("invalid token")
        return token

    def handleRegister(self, payload: oj.Register):
        token = self._check_access_token()
        # TODO check if tokenA is authenticated, otherwise everybody can register
        req_id = request.headers.get("X-Request-ID")
        corr_id = request.headers.get("X-Correlation-ID")

        log.info('got register:' + str(payload))
        client_token = payload['token']
        # - payload contains information to access client (tokenB)
        base, version = self._getSupportedVersion(
            payload['version_url'])
        self._updateService(
            token, client_token, base, version)

        if corr_id is None:
            self._removeService(token)
            # remove tokenA, send new tokenC to enduser
            tokenC = 'Token ' + secrets.token_urlsafe(32)
            data = {'token': tokenC, 'version_url': self.version_urls}

            version_url, version = self._getSupportedVersion(
                payload['version_url'])

            self._addService(  # add version
                tokenC, payload['token'], version_url, version)
            try:
                response = requests.post(version_url+'/register', json=data,
                                         headers={'Authorization': payload['token'],
                                                  'X-Request-ID': secrets.token_urlsafe(8),
                                                  'X-Correlation-ID': req_id})
                log.debug(
                    f"send register to {base + '/register'} with auth: {payload['token']}")
                # TODO request-ID
                if response.status_code >= 205:
                    raise Exception(response.json())
            except Exception:
                log.exception("error in register handling")
                log.warning(tokenC)
                # show token to enter in UI
        log.info(self.endpoints)

    def updateEndpoint(self, payload: oj.Register):
        token = self._check_access_token()
        log.info('update endpoint url for:' + str(token))
        if token in self.endpoints.keys():
            self.endpoints[token]['register'] = payload
        # no user feedback specified. Will always return 204..

    def unregister(self):
        token = self._check_access_token()
        log.info('unregistering ' + str(token) + '. Goodbye')
        self._removeService(token)

    def handleHandshake(self, payload: oj.Handshake):
        token = self._check_access_token()
        self._setRequiredBehavior(
            token, payload['required_behaviour'], new=True)
        log.info('handshake request for token ' + str(token))

        # TODO always reply with 403 if not handshaked yet

    def handleHandshakeAck(self, payload: oj.HandshakeAcknowledgement):
        token = self._check_access_token()
        self._setRequiredBehavior(
            token, payload['required_behaviour'], new=False)
        log.info('handshake_ack received for token ' + str(token))
        # TODO set up heartbeat job (somehow use a listener)
        pass

    def handleHeartbeat(self, payload: oj.Heartbeat):
        token = self._check_access_token()
        offline_at = datetime.strptime(
            payload['offline_mode_at'], "%Y-%m-%d %H:%M:%S")
        self._setOfflineAt(token, offline_at)
        # TODO setup online/offline listener
        log.info(f"got a heartbeat. Will be offline at: {offline_at}")

    def _getSupportedVersion(self, version_urls):
        # TODO check if any client version is supported by us
        # compare with self.version_urls
        return version_urls[0]['base_url'], version_urls[0]['version']

    def _send_heartbeat(self, base_url, interval, token):
        next_heartbeat = datetime.now()+timedelta(seconds=interval)
        log.info('send heartbeat to '+base_url)
        offline_at = datetime.now()+3*timedelta(seconds=interval)
        data = {'offline_mode_at': offline_at.strftime(
            "%Y-%m-%d %H:%M:%S")}
        try:
            requests.post(
                base_url+'/heartbeat',
                headers={'Authorization': token,
                         'X-Request-ID': secrets.token_urlsafe(8)},
                json=data)
        except:
            log.debug('sent heartbeat failed: '+base_url)

        return next_heartbeat

    def _send_ack(self, base_url, interval, token):
        log.info('send ack for '+str(token))
        # send ack for new handshakes

        data = {}  # not interested in heartbeats
        data = {'required_behaviour': {
            'heartbeat_interval': interval}}
        try:
            requests.post(
                base_url+'/handshake_acknowledgment',
                headers={
                    'Authorization': token, 'X-Request-ID': secrets.token_urlsafe(8)},
                json=data)
        except requests.exceptions.ConnectionError:
            log.error("connection failed")

    def _send_register(self, base_url, new_token, client_token):
        try:
            log.info('send register to '+base_url)

            data = {'token': new_token,
                    'version_url': self.version_urls}

            requests.post(
                base_url+'/register',
                headers={'Authorization': client_token,
                         'X-Request-ID': secrets.token_urlsafe(8)},
                json=data)
        except ConnectionError:
            log.error("connection failed")
        except Exception as e:
            log.exception(e)

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
        url = ""
        if token == None and group_id == None:
            log.error('Either token or group_id must be given.')
        else:
            if group_id and token == None:
                token = self._token_by_group_id(group_id)
        if token:
            url = self._url_by_token(token)

        log.info(f'URL: {url}')
        return url

    def isRegistered(self, token):
        raise NotImplementedError()

    def _addService(self, token, client_token, client_url, version=None):
        raise NotImplementedError()

    def _updateService(self, token, client_token=None, client_url=None, version=None):
        raise NotImplementedError()

    def _setGroupIds(self, token, group_ids):
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


class RegistrationDictMan(RegistrationMan):
    def __init__(self, version_urls):
        self._endpoints = {}
        super().__init__(version_urls)

    def _addService(self, token, client_token, client_url, version=None):
        self._endpoints[token] = {'register':
                                  {'token': client_token,
                                   'version_url': client_url}
                                  }
        log.debug(self._endpoints)

    def _updateService(self, token, client_token=None, client_url=None, version=None):
        data = {'register':
                {'token': client_token,
                 'version_url': client_url}
                }
        # updates client_token and version_url without touching other stuff
        self._endpoints[token].update(data)

    def _setGroupIds(self, token, group_ids):
        self._endpoints[token].update({"group_ids": group_ids})

    def _setRequiredBehavior(self, token, required_behavior, new=True):
        self._endpoints[token]['new'] = new
        self._endpoints[token]['required_behavior'] = required_behavior

    def _removeService(self, token):
        self._endpoints.pop(token)

    def isRegistered(self, token):
        return token in self._endpoints

    def _setOfflineAt(self, token, offline_at):
        self._endpoints[token]['offline_at'] = offline_at

    def _token_by_group_id(self, group_id):
        token = None
        for t, v in self._endpoints.items():
            if group_id in v['group_ids']:
                log.info(f'Found token: {t} for group_id: {group_id}')
                token = t
        return token

    def _url_by_token(self, token):
        return self._endpoints[token]['register']['version_url'][0]['base_url'] + '/' + \
            self._endpoints[token]['register']['version_url'][0]['version']

    def _background_job(self):
        #log.debug(self._endpoints)
        for endpoint in self._endpoints.values():
            try:
                base_url = endpoint['register']['version_url']
                if endpoint.get('new') == True:
                    # send ack for new handshakes

                    interval = endpoint['required_behavior']['heartbeat_interval']
                    token = endpoint['register']['token']
                    self._send_ack(base_url, interval, token)

                    endpoint['new'] = False
                    log.debug('send ack to ' + str(endpoint))

                if endpoint.get('required_behavior') != None:
                    nb = endpoint.get('next_heartbeat')
                    if nb is None or (nb < datetime.now()):
                        # next heartbeat is due, send it

                        interval = endpoint['required_behavior']['heartbeat_interval']
                        token = endpoint['register']['token']
                        endpoint['next_heartbeat'] = self._send_heartbeat(
                            base_url, interval, token)

                offline_at = endpoint.get('offline_at')
                if offline_at != None and offline_at < datetime.now():
                    log.debug(
                        base_url + ' endpoint is offline. No Heartbeat received before' + offline_at)
            except Exception:
                log.exception('OSCP background job failed this time')