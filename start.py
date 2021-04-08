#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 28 18:48:33 2021
@author: rottschaefer
backend app for capacity provider
"""
from datetime import datetime
from oscp import createBlueprint
from packaging import version

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
        self.measurement_configuration = None  # Is set up with the handshake acknowledgement

        # Offline Detection
        self.offline = True  # Set to False with the first heartbeat? or after handshake.
        self.lastOnline = None  # Set with first heartbeat
        self.offlineAt = None  # Set with first heartbeat

    def heartbeat(self, heartbeat):
        self.offline = False
        self.lastOnline = datetime.now()
        self.offlineAt = datetime.fromisoformat(heartbeat['offline_mode_at'])  # ohoh wird das korrekt sein?

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

    def registerEndpoint(self, reg):
        self.endpoints.append(Endpoint(reg))


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
    injected_objects = {'endpointmanager': epm,
                        'forecastmanager': cpm,
                        'flexibilityprovider': fpm,
                        'capacityprovider': cpm,
                        'capacityoptimizer': com}

    # the injected_objects are used to route requests from the namespace to the
    # logic containing classes like ForecastManager
    blueprint = createBlueprint(injected_objects, actors=['cp'])

    # using a blueprint allows us to initialize everything without an app context
    # this is cleaner, as the oscp module never needs access to the actual Flask server
    app.register_blueprint(blueprint)

    app.run()