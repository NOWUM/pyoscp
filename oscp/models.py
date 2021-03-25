#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 00:21:29 2021

@author: maurer

This module contains representation of used Enums and Classes from OSCP
"""

from flask_restx import fields, Model


forecastedblock_unit_type = ['A', 'W', 'KW', 'WH', 'KWH']

phase_indicator_type = ['UNKNOWN', 'ONE', 'TWO', 'THREE', 'ALL']

capacity_forecast_type = ['CONSUMPTION',
                          'GENERATION',
                          'FALLBACK_CONSUMPTION',
                          'FALLBACK_GENERATION',
                          'OPTIMUM']

ForecastedBlock = Model('ForecastedBlock',  {
    'capacity': fields.String(description='The id of the area in which the Flexibility Provider has Flexibility Resources connected to the grid.'),
    'phase': fields.String(enum=phase_indicator_type, description='Identifies the phase that the forecast is meant for.'),
    'unit': fields.String(enum=forecastedblock_unit_type, description='Unit of the capacity value.'),
    'start_time': fields.DateTime(),
    'end_time': fields.DateTime(),

})

GroupCapacityForecast = Model('UpdateGroupCapacityForecast', {
    'group_id': fields.String(description='The id of the area in which the Flexibility Provider has Flexibility Resources connected to the grid.'),
    'type': fields.String(enum=capacity_forecast_type, description='Identifies the type of forecast.'),
    'forecasted_blocks': fields.List(fields.Nested(ForecastedBlock),description='The technical content of this message. Describes the amound and period of the to be adjusted capacity'),
})


# models must be registered at a namespace. 
# If the API is somehow using a given model, you should add it to the array
def add_models_to__namespace(namespace):
    for model in [GroupCapacityForecast, ForecastedBlock]:
        namespace.models[model.name] = model
