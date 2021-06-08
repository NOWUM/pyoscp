#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 23 18:51:50 2021

@author: maurer
"""

from flask_restx import Model, fields
from .json_models import phase_indicator, capacity_forecast_type

ext_forecasted_block_unit = ['A', 'W', 'KW', 'WH', 'KWH', 'EUR', 'EUR/KWH', 'EUR/KW']

ExtForecastedBlock = Model('ForecastedBlock', {
    'capacity': fields.Float(description='The value of the forecast.'),
    'phase': fields.String(enum=phase_indicator,  # optional
                           description='Identifies the phase that the forecast is meant for.'),
    'unit': fields.String(enum=ext_forecasted_block_unit, description='Unit of the capacity value.'),
    'start_time': fields.DateTime(),
    'end_time': fields.DateTime(),
})

GroupCapacityPrice = Model('UpdateGroupCapacityPrice', {
    'group_id': fields.String(
        description='The id of the area in which the Flexibility Provider has Flexibility Resources connected to the grid.'),
    'type': fields.String(enum=capacity_forecast_type, default='CONSUMPTION', description='Identifies the type of forecast.'),
    'forecasted_blocks': fields.List(fields.Nested(ExtForecastedBlock),
                                     description='The technical content of this message. Describes the amount and period of the to be adjusted capacity')
})