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


class RegistrationMan():

    def __init__(self, version_urls: list):
        self.endpoints = {}
        test_register = {"token": "TESTTOKEN",
                         "version_url": [
                             {
                                 "version": "2.0",
                                 "base_url": "http://127.0.0.1:5000/oscp/cp"
                             }
                         ]}
        self.endpoints.update({'TESTTOKEN': {'register': test_register}})
        # and ['group_id1'] from dso1.json
        self.endpoints['TESTTOKEN'].update({"group_ids": ['TESTGROUPID']})

        self.version_urls = version_urls
        # run background job every 5 seconds
        self.__stop_thread = False

        def bck_job():
            ticker = threading.Event()
            while not ticker.wait(5):
                self.background_job()
                if self.__stop_thread:
                    break

        self.t = threading.Thread(target=bck_job, daemon=True)

    def start(self):
        log.warning('backgroundjob started')
        self.t.start()

    def stop(self):
        log.info('backgroundjob stopped')
        self.__stop_thread = True

    def _check_access_token(self):
        token = request.headers.get("Authorization")
        if not token:
            raise Unauthorized(description="Unauthorized")

        if not token in self.endpoints.keys():
            raise Forbidden(description="not authorized")
        return token

    def handleRegister(self, payload: oj.Register):
        req_id = request.headers.get("X-Request-ID")
        corr_id = request.headers.get("X-Correlation-ID")
        # tokenA = request.headers.get("Authorization")
        # TODO check if tokenA is authenticated, otherwise everybody can register
        log.info('got register:' + str(payload))
        tokenC = 'Token ' + secrets.token_urlsafe(32)
        # <- payload contains information to access client (tokenB)
        self.endpoints[tokenC] = {'register': payload}
        # TODO check version use latest version
        base = payload['version_url'][0]['base_url']
        data = {'token': tokenC, 'version_url': self.version_urls}

        if corr_id is None:
            try:
                response = r.post(base + '/register', json=data,
                                  headers={'Authorization': payload['token'], 'X-Request-ID': '5',
                                           'X-Correlation-ID': req_id})
                log.debug(
                    f"send register to {base + '/register'} with auth: {payload['token']}")
                # TODO request-ID
                if response.status_code >= 205:
                    raise Exception(response.json())
            except Exception as e:
                log.error(e)
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
        self.endpoints.pop(token)

    def handleHandshake(self, payload: oj.Handshake):
        token = self._check_access_token()
        self.endpoints[token]['new'] = True
        self.endpoints[token]['req_behavior'] = payload['required_behaviour']
        log.info('handshake request for token ' + str(token))

        # TODO always reply with 403 if not handshaked yet

    def handleHandshakeAck(self, payload: oj.HandshakeAcknowledgement):
        token = self._check_access_token()
        self.endpoints[token]['new'] = False
        self.endpoints[token]['req_behavior'] = payload['required_behaviour']
        log.info('handshake_ack received for token ' + str(token))
        # TODO set up heartbeat job (somehow use a listener)
        pass

    def handleHeartbeat(self, payload: oj.Heartbeat):
        token = self._check_access_token()
        self.endpoints[token]['offline_at'] = datetime.strptime(
            payload['offline_mode_at'], "%Y-%m-%d %H:%M:%S")
        # TODO setup online/offline listener
        log.info("got a heartbeat. Will be offline at:" +
                 str(payload['offline_mode_at']))

    def _getSupportedVersion(self, version_urls):
        # TODO check if any client version is supported by us
        # compare with self.version_urls
        return version_urls[0]['base_url']

    def background_job(self):
        log.info('run backgroundjob')

        for endpoint in self.endpoints.values():
            try:
                base_url = self._getSupportedVersion(
                    endpoint['register']['version_url'])
                if endpoint.get('new') == True:
                    # send ack for new handshakes
                    interval = endpoint['req_behavior']['heartbeat_interval']
                    token = endpoint['register']['token']

                    data = {}  # not interested in heartbeats
                    res = requests.post(base_url + '/handshake_acknowledgment',
                                        headers={'Authorization': token, 'X-Request-ID': '5'}, json=data)
                    log.debug(str(res))
                    endpoint['new'] = False
                    log.info('send ack to ' + str(endpoint))

                if endpoint.get('req_behavior') != None:
                    nb = endpoint.get('next_heartbeat')
                    if nb is None or (nb < datetime.now()):
                        # next heartbeat is due, send it

                        interval = endpoint['req_behavior']['heartbeat_interval']
                        next_heartbeat = datetime.now() + timedelta(seconds=interval)
                        endpoint['next_heartbeat'] = next_heartbeat
                        token = endpoint['register']['token']

                        log.info('send heartbeat to ' +
                                 base_url + ' auth: '+token)
                        offline_at = datetime.now() + 3 * timedelta(seconds=interval)
                        data = {'offline_mode_at': offline_at.strftime(
                            "%Y-%m-%d %H:%M:%S")}
                        res = requests.post(base_url + '/heartbeat', headers={'Authorization': token, 'X-Request-ID': '5'},
                                            json=data)
                        log.info('heartbeat returned: '+str(res.status_code))

                offline_at = endpoint.get('offline_at')
                if offline_at != None and offline_at < datetime.now():
                    log.info(
                        base_url + ' endpoint is offline. No Heartbeat received before' + offline_at)
            except Exception as e:
                log.error(e)

    def getToken(self, group_id):
        token = ""
        for t, v in self.endpoints.items():
            if group_id in v['group_ids']:
                log.info(f'Found token: {t} for group_id: {group_id}')
                token = t
        return token

    def getURL(self, token=None, group_id=None):
        url = ""
        if token == None and group_id == None:
            log.error('Either token or group_id must be given.')
        else:
            if group_id and token == None:
                token = self.getToken(group_id)
        if token:
            url = self.endpoints[token]['register']['version_url'][0]['base_url'] + '/' + \
                self.endpoints[token]['register']['version_url'][0]['version']

        log.info(f'URL: {url}')
        return url

    def isRegistered(self, token):
        reged = bool(self.endpoints.get(token))
        if not reged:
            log.error('### REQUEST FROM UNREGISTERED PARTICIPANT ###')
        return reged