#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 12:32:01 2021

@author: maurer
"""

from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.models import GroupCapacityForecast, ForecastedBlock
import logging

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
forecast_ns = Namespace(name="forecast", validate=True)

forecast_ns.models[GroupCapacityForecast.name] = GroupCapacityForecast
forecast_ns.models[ForecastedBlock.name] = ForecastedBlock

# this is the same as the following code would do:
# add_models_to__namespace(forecast_ns)

# now we have our first api route. This 
@forecast_ns.route('/update_group_capacity_forecast', doc={"description": "API Endpoint for Session management"})
@forecast_ns.route('/adjust_group_capacity_forecast', doc={"description": "API Endpoint for Session management"})
@forecast_ns.response(204, 'No Content')
class updateGroupCapacityForecast(Resource):

    def __init__(self, api=None, *args, **kwargs):
        # forecastmanager is a black box dependency, which contains the logic
        self.forecastmanager = kwargs['forecastmanager']
        super().__init__(api, *args, **kwargs)

    @forecast_ns.expect(GroupCapacityForecast)
    @forecast_ns.marshal_with(GroupCapacityForecast)
    # @forecast_ns.response(204, 'No Content')
    def post(self):
        '''
        The message is sent from Capacity Provider to the Flexibility Provider and from Flexibility Provider to Capacity Optimizer which
        should generate an Optimum capacity forecast for the capacity that should be used in the specific group.
        '''

        self.forecastmanager.forecasts.append(forecast_ns.payload)
        # using logging instead of print is threadsafe and non-blocking
        # but you can't add multiple strings and expect that they get joined
        logging.info(str(self.forecastmanager.forecasts))
        return '', 204
