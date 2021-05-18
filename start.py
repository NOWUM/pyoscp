#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 28 18:48:33 2021
@author: rottschaefer
backend app for capacity provider
"""
import logging
import os
import json
from oscp import createBlueprint
from flask import Flask, redirect
from oscp.RegistrationManager import RegistrationDictMan

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('oscp')


class FlexibilityManager(object):

    def __init__(self):
        self.endpoints = []


class CapacityProviderManager():

    def __init__(self):
        self.stuff = []


class FlexibilityProviderManager():

    def __init__(self):
        self.stuff = []


class CapacityOptimizerManager():

    def __init__(self):
        self.stuff = []


class EnergyProviderManager():

    def __init__(self):
        pass


app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def home():
    # return redirect('/oscp/fp/2.0/ui')
    return redirect('/oscp/ui')


# inject dependencies here
cpm = CapacityProviderManager()
com = CapacityOptimizerManager()
fpm = FlexibilityProviderManager()
epm = EnergyProviderManager()

HOST_URL = os.getenv('HOST_URL', 'http://localhost:5000')
version_urls = [{'version': '2.0', 'base_url': HOST_URL + '/oscp/fp/2.0'}]
regman = RegistrationDictMan(version_urls)
injected_objects = {'energyprovider': epm,
                    'capacityprovider': cpm,
                    'capacityoptimizer': com,
                    'flexibilityprovider': fpm,
                    'registrationmanager': regman}

config = 'oscp.json'
if os.path.exists(config):
    log.info(f'reading config file {config}')
    with open(config, 'r') as f:
        conf = json.load(f)
        regman._addService(conf['token'], None, None)
else:
    log.info(f'config file {config} does not exist')


# the injected_objects are used to route requests from the namespace to the
# logic containing classes like ForecastManager
blueprint = createBlueprint(injected_objects)  # , actors=['co'])

# using a blueprint allows us to initialize everything without an app context
# this is cleaner, as the oscp module never needs access to the actual Flask server
app.register_blueprint(blueprint)

if __name__ == '__main__':
    regman.start()
    app.run()

    regman.stop()