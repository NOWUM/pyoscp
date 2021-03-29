#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 28 18:48:33 2021
@author: rottschaefer
backend app for capacity provider
"""

from oscp import createBlueprint
from oscp.json_models import Register


from packaging import version

class Endpoint(dict):

    # always communicate with latest version available
    def _getLatestVersion(self, version_urls):
        latest = version.parse(version_urls[0]['version'])
        baseUrl = version_urls[0]['base_url']
        for v in version_urls:
            cur = version.parse(v['version'])
            if  cur > latest:
                baseUrl = v['base_url']
                latest = cur
        return str(latest), baseUrl

    def __init__(self, reg):
        self['token'] = reg['token']
        self['version'], self['base_url'] = self._getLatestVersion(reg['version_url'])

class EndpointManager(object):

    def __init__(self):
        self.endpoints = []

    def addEndpoint(self, reg):
        self.endpoints.append(Endpoint(reg))


# the forecastManager is independent from the communication and should be replacable
# by using different forecastmanagers, we can inject different strategies into the system
class ForecastManager(object):

    def __init__(self):
        self.forecasts = []

    def getForecast(self, value):
        return 30


if __name__ == '__main__':

    from flask import Flask, redirect
    app = Flask(__name__)

    @app.route('/', methods=['POST', 'GET'])
    def home():
        # return redirect('/oscp/fp/2.0/ui')
        return redirect('/oscp/ui')

    # inject dependencies here
    fcm = ForecastManager()
    epm = EndpointManager()
    injected_objects = {'db': 'db_test',
                        'endpointmanager': epm,
                        'forecastmanager': fcm}

    # the injected_objects are used to route requests from the namespace to the
    # logic containing classes like ForecastManager
    blueprint = createBlueprint(injected_objects, actors=['cp'])

    # using a blueprint allows us to initialize everything without an app context
    # this is cleaner, as the oscp module never needs access to the actual Flask server
    app.register_blueprint(blueprint)

    app.run()
