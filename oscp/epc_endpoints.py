#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 27 15:55:51 2021

@author: maurer
"""
from flask_restx import Resource, Namespace
from oscp.registration import namespace_registration
from oscp.json_models import create_header_parser, add_models_to_namespace
from oscp.ep_models import ExtForecastedBlock, GroupCapacityPrice

energy_price_client_ns = Namespace(name="epc", validate=True, path="/ep/2.0")

models = [ExtForecastedBlock, GroupCapacityPrice]

add_models_to_namespace(energy_price_client_ns, models)
header_parser = create_header_parser(energy_price_client_ns)
namespace_registration(energy_price_client_ns)

@energy_price_client_ns.route('/update_group_capacity_price')
@energy_price_client_ns.expect(header_parser)  # validate=True
@energy_price_client_ns.response(204, 'No Content')
@energy_price_client_ns.response(404, 'Not found')
class updateGroupCapacityPrice(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.pricemanager = kwargs['pricemanager']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @energy_price_client_ns.expect(GroupCapacityPrice)
    def post(self):
        """
        Update Load TimeSeries which can contain a Load or a Price (or both).
        Can be used by a EnergyProvider or a DSO to communicate a price series
        """
        token = self.registrationmanager._check_access_token()
        self.pricemanager.handleUpdateGroupLoadForecast(
            energy_price_client_ns.payload, token)
        return '', 204