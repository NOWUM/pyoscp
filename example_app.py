#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 21 21:57:33 2021
@author: maurer
Starter class for pyOCPI test
"""

from oscp import createBlueprint


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
    injected_objects = {'db': 'db_test',
                        'forecastmanager': fcm}

    # the injected_objects are used to route requests from the namespace to the
    # logic containing classes like ForecastManager
    blueprint = createBlueprint(injected_objects)

    # using a blueprint allows us to initialize everything without an app context
    # this is cleaner, as the oscp module never needs access to the actual Flask server
    app.register_blueprint(blueprint)

    app.run()