#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 00:21:29 2021

@author: maurer

This module contains representation of used Enums and Classes from OSCP
"""

from flask_restx import fields, Model

energy_measurement_unit = ['WH', 'KWH']
direction = ['NET', 'IMPORT', 'EXPORT']
energy_type = ['FLEXIBLE', 'NONFLEXIBLE', 'TOTAL']
forecastedblock_unit_type = ['A', 'W', 'KW', 'WH', 'KWH']
measurement_configuration = ['CONTINUOUS', 'INTERMITTENT']
phase_indicator_type = ['UNKNOWN', 'ONE', 'TWO', 'THREE', 'ALL']
asset_category = ['CHARGING', 'CONSUMPTION', 'GENERATION', 'STORAGE']
capacity_forecast_type = ['CONSUMPTION', 'GENERATION',
                          'FALLBACK_CONSUMPTION', 'FALLBACK_GENERATION', 'OPTIMUM']

RequiredBehaviour = Model('RequiredBehaviour', {
    'heartbeat_interval': fields.Integer(description='Optional. The interval (in seconds) in which the sender of '
                                                     'this response expects heartbeats to receive. If provided, '
                                                     'value must be 1 or higher. If the sender is not interested '
                                                     'in the heartbeat of the receiver, this field can be '
                                                     'omitted.'),
    'measurement_configuration': fields.String(enum=measurement_configuration,
                                               description='For determining how measurements are aggregated. '
                                                           'Providing multiple configurations is allowed. An empty '
                                                           'array represents no configurations.')
})

VersionUrl = Model('VersionUrl', {
    'version': fields.String(description='Mandatory. The OSCP version, e.g. 2.0.'),
    'base_url': fields.Url(description='Mandatory. The base url for this version, e.g. https://oscp/cp/2.0.')
})

Register = Model('Register', {
    'token': fields.String(description='The token for the other party to authenticate in your system.'),
    'version_url': fields.List(fields.Nested(VersionUrl),
                               description='The initiator of the registration sends in this field the OSCP versions '
                                           'that it supports with associated base URLs. When used as a reply, '
                                           'it contains the OSCP version that is selected, with the associated base '
                                           'url.')
})

Handshake = Model('Handshake', {
    'required_behaviour': fields.Nested(RequiredBehaviour)
})

HandshakeAcknowledgement = Model('HandshakeAcknowledgement', {
    'required_behaviour': fields.Nested(RequiredBehaviour)
})

Heartbeat = Model('Heartbeat', {
    'offline_mode_at': fields.DateTime()
})

ForecastedBlock = Model('ForecastedBlock', {
    'capacity': fields.Float(description='The value of the forecast.'),
    'phase': fields.String(enum=phase_indicator_type,
                           description='Identifies the phase that the forecast is meant for.'),
    'unit': fields.String(enum=forecastedblock_unit_type, description='Unit of the capacity value.'),
    'start_time': fields.DateTime(),
    'end_time': fields.DateTime(),

})

GroupCapacityForecast = Model('UpdateGroupCapacityForecast', {
    'group_id': fields.String(
        description='The id of the area in which the Flexibility Provider has Flexibility Resources connected to the '
                    'grid.'),

    'type': fields.String(enum=capacity_forecast_type, description='Identifies the type of forecast.'),

    'forecasted_blocks': fields.List(fields.Nested(ForecastedBlock),
                                     description='The technical content of this message. Describes the amound and period of the to be adjusted '
                                                 'capacity'),
})

AdjustGroupCapacityForecast = Model('AdjustGroupCapacityForecast', {
    'group_id': fields.String(
        description='The id of the area in which the Flexibility Provider has Flexibility Resources connected to the '
                    'grid.'),

    'type': fields.String(enum=capacity_forecast_type, description='Identifies the type of forecast.'),

    'forecasted_blocks': fields.List(fields.Nested(ForecastedBlock),
                                     description='The technical content of this message. Describes the amount and period of the to be adjusted '
                                                 'capacity'),
})

GroupCapacityComplianceError = Model('GroupCapacityComplianceError', {
    'message': fields.String(
        description='This message is for notifying the Capacity Provider the Flexibility Provider cannot comply to '
                    'the Capacity Forecast within an UpdateGroupCapacityForecast message.'),

    'forecasted_blocks': fields.List(fields.Nested(ForecastedBlock),
                                     description='Optional. The list of forecast blocks that FP cannot comply to.')
})

Measurements = Model('Measurements', {
    'value': fields.Float(),
    'phase': fields.String(enum=phase_indicator_type,
                           description='Identifies the phase that the forecast is meant for.'),
    'unit': fields.String(enum=energy_measurement_unit, description='A unit of energy measurement.'),
    'direction': fields.String(enum=direction, description='Indicates the direction the energy has flown into ('
                                                           'import, export or net).'),
    'energy_type': fields.String(enum=energy_type, description='Indicates whether flexible, non-flexible or total '
                                                               'energy is reported. When absent, '
                                                               'TOTAL is assumed.'),
    'measure_time': fields.DateTime(),
    'initial_measure_time': fields.DateTime()
})

UpdateGroupMeasurements = Model('UpdateGroupMeasurements', {
    'group_id': fields.String(
        description='The id of the area in which the Flexibility Provider has Flexibility Resources connected to the '
                    'grid.'),
    'measurements': fields.Nested(Measurements)
})


# models must be registered at a namespace.
# If the API is somehow using a given model, you should add it to the array
def add_models_to_namespace(namespace, models):
    for model in models:
        namespace.models[model.name] = model

def create_header_parser(namespace):
    header_parser = namespace.parser()
    header_parser.add_argument('Authorization', required=True, location='headers')
    header_parser.add_argument('X-Request-ID', required=True, location='headers')
    header_parser.add_argument('X-Correlation-ID', location='headers')
    header_parser.add_argument('X-Segment-Index', location='headers')
    header_parser.add_argument('X-Segment-Count', location='headers')
    return header_parser