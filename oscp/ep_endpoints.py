#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask_restx import Resource, Namespace
from oscp.registration import namespace_registration
from oscp.json_models import create_header_parser, add_models_to_namespace, GroupCapacityForecast
from oscp.ep_models import ExtForecastedBlock, GroupCapacityPrice

energy_price_ns = Namespace(name="ep", validate=True, path="/ep/2.0")

models = [ExtForecastedBlock, GroupCapacityPrice, GroupCapacityForecast]

add_models_to_namespace(energy_price_ns, models)
header_parser = create_header_parser(energy_price_ns)
namespace_registration(energy_price_ns)

@energy_price_ns.route('/request_capacity_price')
@energy_price_ns.expect(header_parser)  # validate=True
@energy_price_ns.response(200, 'Ok')
@energy_price_ns.response(400, 'Cant comply')
@energy_price_ns.response(404, 'Not found')
class requestCapacityPrice(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.pricemanager = kwargs['pricemanager']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @energy_price_ns.expect(GroupCapacityForecast)
    @energy_price_ns.marshal_with(GroupCapacityPrice)
    def post(self):
        """
        Get Price Series for the electricity of a given LoadSeries Request
        """
        token = self.registrationmanager._check_access_token()
        return self.pricemanager.handleRequestCapacityPrice(
            energy_price_ns.payload, token)