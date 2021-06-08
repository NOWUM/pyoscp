#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask_restx import Resource
from oscp.json_models import create_header_parser, add_models_to_namespace, GroupCapacityForecast
from oscp.ep_models import ExtForecastedBlock, GroupCapacityPrice

models = [ExtForecastedBlock, GroupCapacityPrice, GroupCapacityForecast]


def addPrice(namespace):
    add_models_to_namespace(namespace, models)
    header_parser = create_header_parser(namespace)

    @namespace.route('/request_capacity_price')
    @namespace.expect(header_parser)  # validate=True
    @namespace.response(200, 'Ok')
    @namespace.response(400, 'Cant comply')
    @namespace.response(404, 'Not found')
    class requestCapacityPrice(Resource):
        def __init__(self, api=None, *args, **kwargs):
            self.capacityprovider = kwargs['capacityprovider']
            self.registrationmanager = kwargs['registrationmanager']
            super().__init__(api, *args, **kwargs)

        @namespace.expect(GroupCapacityForecast)
        @namespace.marshal_with(GroupCapacityPrice)
        def post(self):
            """
            Get Price Series for the electricity of a given LoadSeries Request
            """
            token = self.registrationmanager._check_access_token()
            return self.capacityprovider.handleRequestCapacityPrice(namespace.payload, token)
