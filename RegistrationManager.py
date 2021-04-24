import secrets
import requests as r
import oscp.json_models as oj
import logging
from werkzeug.exceptions import Unauthorized, Forbidden
import requests
import threading
from flask import request
from datetime import datetime, timedelta


class RegistrationMan():

    def __init__(self, version_urls: list):
        self.endpoints = {}
        self.group_ids = {}
        self.version_urls = version_urls
        # run background job every 5 seconds
        self.stop_thread = False

        def bck_job():
            ticker = threading.Event()
            while not ticker.wait(5):
                self.background_job()
                if self.stop_thread:
                    break

        self.t = threading.Thread(target=bck_job, daemon=True)
        self.t.start()

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
        logging.info('got register:' + str(payload))
        tokenC = 'Token ' + secrets.token_urlsafe(32)
        # <- payload contains information to access client (tokenB)
        self.endpoints[tokenC] = {'register': payload}
        # TODO link group_ids to the registration of tokenA
        # like: self.endpoints[tokenC]['group_ids'] = ['group_id_0', 'group_id_1']
        # of better: map tokens to group_ids
        # like self.group_ids[group_id] = ['tokenC_0', 'tokenC_1']
        # TODO check version use latest version
        base = payload['version_url'][0]['base_url']
        data = {'token': tokenC, 'version_url': self.version_urls}

        if corr_id is not None:
            try:
                response = r.post(base + '/register', json=data,
                                  headers={'Authorization': payload['token'], 'X-Request-ID': '5',
                                           'X-Correlation-ID': req_id})
                # TODO request-ID
                if response.status_code >= 205:
                    raise Exception(response.json())
            except Exception as e:
                logging.error(e)
                logging.warn(tokenC)
                # show token to enter in UI
        logging.info(self.endpoints)

    def updateEndpoint(self, payload: oj.Register):
        token = self._check_access_token()
        logging.info('update endpoint url for:' + str(token))
        if token in self.endpoints.keys():
            self.endpoints[token]['register'] = payload
        # no user feedback specified. Will always return 204..

    def unregister(self):
        token = self._check_access_token()
        logging.info('unregistering ' + str(token) + '. Goodbye')
        self.endpoints.pop(token)

    def handleHandshake(self, payload: oj.Handshake):
        token = self._check_access_token()
        self.endpoints[token]['new'] = True
        self.endpoints[token]['req_behavior'] = payload['required_behaviour']
        logging.info('handshake request for token ' + str(token))

        # TODO always reply with 403 if not handshaked yet

    def handleHandshakeAck(self, payload: oj.HandshakeAcknowledgement):
        token = self._check_access_token()
        self.endpoints[token]['new'] = False
        self.endpoints[token]['req_behavior'] = payload['required_behaviour']
        logging.info('handshake_ack received for token ' + str(token))
        # TODO set up heartbeat job (somehow use a listener)
        pass

    def handleHeartbeat(self, payload: oj.Heartbeat):
        token = self._check_access_token()
        self.endpoints[token]['offline_at'] = datetime.strptime(payload['offline_mode_at'], "%Y-%m-%d %H:%M:%S")
        # TODO setup online/offline listener
        logging.info("got a heartbeat. Will be offline at:" +
                     str(payload['offline_mode_at']))

    def _getSupportedVersion(self, version_urls):
        # TODO check if any client version is supported by us
        # compare with self.version_urls
        return version_urls[0]['base_url']

    def background_job(self):
        # logging.info('background job running')

        for endpoint in self.endpoints.values():
            try:
                base_url = self._getSupportedVersion(endpoint['register']['version_url'])
                if endpoint.get('new') == True:
                    # send ack for new handshakes
                    interval = endpoint['req_behavior']['heartbeat_interval']
                    token = endpoint['register']['token']

                    data = {}  # not interested in heartbeats
                    requests.post(base_url + '/handshake_acknowledgment',
                                  headers={'Authorization': token, 'X-Request-ID': '5'}, json=data)
                    endpoint['new'] = False
                    logging.info('send ack to ' + str(endpoint))

                if endpoint.get('req_behavior') != None:
                    nb = endpoint.get('next_heartbeat')
                    if nb is None or (nb < datetime.now()):
                        # next heartbeat is due, send it

                        interval = endpoint['req_behavior']['heartbeat_interval']
                        next_heartbeat = datetime.now() + timedelta(seconds=interval)
                        endpoint['next_heartbeat'] = next_heartbeat
                        token = endpoint['register']['token']

                        logging.info('send heartbeat to ' + base_url)
                        offline_at = datetime.now() + 3 * timedelta(seconds=interval)
                        data = {'offline_mode_at': offline_at.strftime("%Y-%m-%d %H:%M:%S")}
                        requests.post(base_url + '/heartbeat', headers={'Authorization': token, 'X-Request-ID': '5'},
                                      json=data)

                offline_at = endpoint.get('offline_at')
                if offline_at != None and offline_at < datetime.now():
                    logging.info(base_url + ' endpoint is offline. No Heartbeat received before' + offline_at)
            except Exception as e:
                logging.error('Error processing endpoint' + endpoint['token'])
                logging.error(e)

    def getEndpoint(self, group_id):
        endpoint = None
        for k, v in self.endpoints.items():
            if group_id in v['group_ids']:
                endpoint = v
        return endpoint
