#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 27 15:55:51 2021

@author: maurer
"""
from flask_restx import Resource
from oscp.json_models import create_header_parser, add_models_to_namespace
from oscp.ep_models import ExtForecastedBlock, GroupCapacityPrice


def addForPriceCalculation(namespace):
    models = [ExtForecastedBlock, GroupCapacityPrice]

    add_models_to_namespace(namespace, models)
    header_parser = create_header_parser(namespace)

    @namespace.route('/update_group_capacity_price')
    @namespace.expect(header_parser)  # validate=True
    @namespace.response(204, 'No Content')
    @namespace.response(404, 'Not found')
    class updateGroupCapacityPrice(Resource):
        def __init__(self, api=None, *args, **kwargs):
            self.pricemanager = kwargs['pricemanager']
            self.registrationmanager = kwargs['registrationmanager']
            super().__init__(api, *args, **kwargs)

        @namespace.expect(GroupCapacityPrice)
        def post(self):
            """
            Update Load TimeSeries which can contain a Load or a Price (or both).
            Can be used by a EnergyProvider or a DSO to communicate a price series
            """
            token = self.registrationmanager._check_access_token()
            self.pricemanager.handleUpdateGroupCapacityPrice(
                namespace.payload, token)
            return '', 204