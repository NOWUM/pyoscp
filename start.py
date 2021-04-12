#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 28 18:48:33 2021
@author: rottschaefer
backend app for capacity provider
"""
from typing import List
import secrets
import requests as r
import oscp.json_models as oj
import logging
from datetime import datetime
from oscp import createBlueprint
from packaging import version
from flask import request

"""
Grundlegende Datenbasis des gesamten Netz
Informationen mit allen Netzanschlusspunkten, inkl.
 * maximaler Kapazität
 * genutzter Kapatität
 * maximaler Flexibilität
 * genutzter Flexibilität
 * registrierten Flexibilitäten

Macht hier für Forecasts eine Zeitreihe Sinn?
Macht ein Pandas Dataframe Sinn?
"""
grid_data = []


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

class RegistrationMan():
    def __init__(self, version_urls: list):
        self.endpoints = {}
        self.handshaked = {}
        self.heartbeats = {}
        self.version_urls = version_urls

    def _check_access_token(self):
        token = request.headers.get("Authorization")
        if not token:
            raise Unauthorized(description="Unauthorized")

        if not token in self.endpoints.keys():
            raise Forbidden(description="not authorized")
        return token

    def handleRegister(self, payload: oj.Register):
        #tokenA = request.headers.get("Authorization")
        # TODO check if tokenA is authenticated, otherwise everybody can register
        logging.warning('got register:'+str(payload))
        tokenC = 'Token '+secrets.token_urlsafe(32)
        # <- payload contains information to access client (tokenB)
        self.endpoints[tokenC] = payload
        # TODO check version use latest version
        base = payload['version_url'][0]['base_url']
        # check if base is in version_urls, to mitigate possible DoS through recursion
        data = {'token': tokenC, 'version_url': self.version_urls}

        try:
            response = r.post(base+'/register', json=data,
                              headers={'Authorization': payload['token'], 'X-Request-ID': '5'})
            # TODO request-ID
            if response.status_code >= 205:
                raise Exception(response.json())
        except Exception as e:
            logging.error(e)
            logging.warn(tokenC)
            # show token to enter in UI

    def updateEndpoint(self, payload: oj.Register):
        token = self._check_access_token()
        if token in self.endpoints.keys():
            self.endpoints[token] = payload
        # no user feedback specified. Will always return 204..

    def unregister(self):
        token = self._check_access_token()
        self.endpoints.pop(token)

    def handleHandshake(self, payload: oj.Handshake):
        token = self._check_access_token()
        self.handshaked[token] = payload['required_behaviour']
        # TODO set up heartbeat job and send handshakeack (somehow use a listener)

        # TODO always reply with 403 if not handshaked yet

    def handleHandshakeAck(self, payload: oj.HandshakeAcknowledgement):
        token = self._check_access_token()
        self.handshaked[token] = payload['required_behaviour']
        # TODO set up heartbeat job (somehow use a listener)
        pass

    def handleHeartbeat(self, payload: oj.Heartbeat):
        token = self._check_access_token()
        self.heartbeats[token] = payload['offline_mode_at']
        # TODO setup online/offline listener here
        logging.info("got a heartbeat. Will be offline at:" +
                     str(payload['offline_mode_at']))


if __name__ == '__main__':

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

    app.run()