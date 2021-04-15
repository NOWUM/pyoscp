#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 28 18:48:33 2021
@author: rottschaefer
backend app for capacity provider
"""
import secrets
import requests as r
import oscp.json_models as oj
import logging
from datetime import datetime, timedelta
from oscp import createBlueprint
from packaging import version
from flask import request


class Endpoint(object):

    # always communicate with latest version available
    def _getLatestVersion(self, version_urls):
        latest = version.parse(version_urls[0]['version'])
        baseUrl = version_urls[0]['base_url']
        for v in version_urls:
            cur = version.parse(v['version'])
            if cur > latest:
                baseUrl = v['base_url']
                latest = cur
        return str(latest), baseUrl

    def __init__(self, reg):
        self.token = reg['token']
        self.version, self.base_url = self._getLatestVersion(
            reg['version_url'])

        # Handshake and Acknowledgement
        self.heartbeat_interval = None  # Is set up with the handshake acknowledgement
        self.acknowledged = False
        # Is set up with the handshake acknowledgement
        self.measurement_configuration = None

        # Offline Detection
        # Set to False with the first heartbeat? or after handshake.
        self.offline = True
        self.lastOnline = None  # Set with first heartbeat
        self.offlineAt = None  # Set with first heartbeat

    def heartbeat(self, heartbeat):
        self.offline = False
        self.lastOnline = datetime.now()
        self.offlineAt = datetime.fromisoformat(
            heartbeat['offline_mode_at'])  # ohoh wird das korrekt sein?

    def initHandshake(self, handshake):
        """
        Initializing the handshake with a newly registered endpoint to settle configurations.
        Required Behaviour contains the heartbeat interval and the measurement configuration
        :param handshake: {
            "required_behaviour": {
                "heartbeat_interval": int,
                "measurement_configuration": [{
                    "enum": ["CONTINUOUS", "INTERMITTENT"]}
                ]}
            }
        :return:
        """

        # call /handshake endpoint at flexibility provider and transmit the required_behaviour dict.
        return

    def acknowledgeHandshake(self, behaviour):
        # Receive handshake acknowledgement from felxibility provider
        pass


class Flexibility(object):

    def __init__(self, ID: str, ep: Endpoint):
        self.groupId = ID
        self.endpoint = ep
        self.forecastedBlocks = []
        self.maxCapacity = None
        self.minCapacity = None
        self.maxFlexibility = None

    def updateForecastedBlocks(self, fcb):
        # After calculating the transmission capabilities and grid status,
        # the individual flexibilities need to be updated
        pass


class FlexibilityManager(object):

    def __init__(self):
        self.endpoints = []

    def handleRegister(self, reg):
        self.endpoints.append(Endpoint(reg))

    def updateEndpoint(self, payload):
        pass

    def unregister(self):
        pass

    def handleHandshake(self, payload):
        pass

    def handleHandshakeAck(self, payload):
        pass

    def handleHeartbeat(self, payload):
        logging.info("got a heartbeat")


class CapacityProviderManager():

    def __init__(self):
        self.stuff = []

    def handleAdjustGroupCapacityForecast(self, value):
        pass

    def handleGroupCapacityComplianceError(self, value):
        pass

    def handleUpdateGroupMeasurements(self, payload):
        pass


class FlexibilityProviderManager():

    def __init__(self):
        self.stuff = []

    def handleUpdateGroupCapacityForecast(self, value):
        pass


class CapacityOptimizerManager():

    def __init__(self):
        self.stuff = []

    def handleUpdateGroupCapacityForecast(self, value):
        pass

    def handleUpdateAssetMeasurements(self, value):
        pass


from werkzeug.exceptions import Unauthorized, Forbidden
import requests
import threading


class RegistrationMan():

    def __init__(self, version_urls: list):
        self.endpoints = {}
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
        #tokenA = request.headers.get("Authorization")
        # TODO check if tokenA is authenticated, otherwise everybody can register
        logging.info('got register:'+str(payload))
        tokenC = 'Token '+secrets.token_urlsafe(32)
        # <- payload contains information to access client (tokenB)
        self.endpoints[tokenC] = {'register': payload}
        # TODO check version use latest version
        base = payload['version_url'][0]['base_url']
        data = {'token': tokenC, 'version_url': self.version_urls}

        if corr_id != None:
            try:
                response = r.post(base+'/register', json=data,
                                  headers={'Authorization': payload['token'], 'X-Request-ID': '5', 'X-Correlation-ID': req_id})
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
        logging.info('update endpoint url for:'+str(token))
        if token in self.endpoints.keys():
            self.endpoints[token]['register'] = payload
        # no user feedback specified. Will always return 204..

    def unregister(self):
        token = self._check_access_token()
        logging.info('unregistering '+str(token)+'. Goodbye')
        self.endpoints.pop(token)

    def handleHandshake(self, payload: oj.Handshake):
        token = self._check_access_token()
        self.endpoints[token]['new']=True
        self.endpoints[token]['req_behavior']=payload['required_behaviour']
        logging.info('handshake request for token '+str(token))

        # TODO always reply with 403 if not handshaked yet

    def handleHandshakeAck(self, payload: oj.HandshakeAcknowledgement):
        token = self._check_access_token()
        self.endpoints[token]['new']=False
        self.endpoints[token]['req_behavior']=payload['required_behaviour']
        logging.info('handshake_ack received for token '+str(token))
        # TODO set up heartbeat job (somehow use a listener)
        pass

    def handleHeartbeat(self, payload: oj.Heartbeat):
        token = self._check_access_token()
        self.endpoints[token]['offline_at'] = datetime.strptime(payload['offline_mode_at'], "%Y-%m-%d %H:%M:%S")
        # TODO setup online/offline listener
        logging.info("got a heartbeat. Will be offline at:" +
                     str(payload['offline_mode_at']))

    def _getSupportedVersion(self,version_urls):
        # TODO check if any client version is supported by us
        # compare with self.version_urls
        return version_urls[0]['base_url']

    def background_job(self):
        #logging.info('background job running')

        for endpoint in self.endpoints.values():
            try:
                base_url = self._getSupportedVersion(endpoint['register']['version_url'])
                if endpoint.get('new')==True:
                    # send ack for new handshakes
                    interval = endpoint['req_behavior']['heartbeat_interval']
                    token = endpoint['register']['token']

                    data={} # not interested in heartbeats
                    requests.post(base_url+'/handshake_acknowledgment',headers={'Authorization': token, 'X-Request-ID':'5'},json=data)
                    endpoint['new']=False
                    logging.info('send ack to '+str(endpoint))

                if endpoint.get('req_behavior')!=None:
                    nb = endpoint.get('next_heartbeat')
                    if nb==None or (nb<datetime.now()):
                        # next heartbeat is due, send it

                        interval = endpoint['req_behavior']['heartbeat_interval']
                        next_heartbeat=datetime.now()+timedelta(seconds=interval)
                        endpoint['next_heartbeat']=next_heartbeat
                        token = endpoint['register']['token']

                        logging.info('send heartbeat to '+base_url)
                        offline_at =datetime.now()+3*timedelta(seconds=interval)
                        data={'offline_mode_at': offline_at.strftime("%Y-%m-%d %H:%M:%S")}
                        requests.post(base_url+'/heartbeat',headers={'Authorization': token, 'X-Request-ID':'5'},json=data)

                offline_at = endpoint.get('offline_at')
                if offline_at!=None and offline_at<datetime.now():
                    logging.info(base_url+' endpoint is offline. No Heartbeat received before'+offline_at)
            except Exception as e:
                logging.error('Error processing endpoint'+endpoint['token'])
                logging.error(e)


logging.basicConfig(level=logging.INFO)
from flask import Flask, redirect
app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def home():
    # return redirect('/oscp/fp/2.0/ui')
    return redirect('/oscp/ui')

# inject dependencies here
cpm = CapacityProviderManager()
com = CapacityOptimizerManager()
fpm = FlexibilityProviderManager()
epm = FlexibilityManager()

HOST_URL = 'http://localhost:5000'
version_urls = [{'version': '2.0', 'base_url': HOST_URL+'/oscp/fp/2.0'}]
regman = RegistrationMan(version_urls)
injected_objects = {'endpointmanager': epm,
                    'forecastmanager': cpm,
                    'flexibilityprovider': fpm,
                    'capacityprovider': cpm,
                    'capacityoptimizer': com,
                    'registrationmanager': regman}

# the injected_objects are used to route requests from the namespace to the
# logic containing classes like ForecastManager
blueprint = createBlueprint(injected_objects)  # , actors=['co'])

# using a blueprint allows us to initialize everything without an app context
# this is cleaner, as the oscp module never needs access to the actual Flask server
app.register_blueprint(blueprint)

if __name__ == '__main__':

    app.run()

    regman.stop_thread=True