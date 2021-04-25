import logging

import flask
from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from pyoscp.oscp.registration import namespace_registration
from pyoscp.oscp.json_models import (create_header_parser, add_models_to_namespace,
                                     ForecastedBlock, AdjustGroupCapacityForecast,
                                     GroupCapacityComplianceError, UpdateGroupMeasurements,
                                     EnergyMeasurement)

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
cap_provider_ns = Namespace(name="cp", validate=True, path="/cp/2.0")

models = [ForecastedBlock, AdjustGroupCapacityForecast, UpdateGroupMeasurements,
          GroupCapacityComplianceError, EnergyMeasurement]

add_models_to_namespace(cap_provider_ns, models)
header_parser = create_header_parser(cap_provider_ns)
namespace_registration(cap_provider_ns)


@cap_provider_ns.route('/adjust_group_capacity_forecast', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content!!!')
@cap_provider_ns.response(404, 'Not found!')
class adjustGroupCapacityForecast(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.capacityprovider = kwargs['capacityprovider']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(AdjustGroupCapacityForecast)
    def post(self):
        """
        Describe me.
        Please.
        """
        print(f'Headers: {flask.Request.headers}')
        self.capacityprovider.handleAdjustGroupCapacityForecast(cap_provider_ns.payload)
        return '', 204


@cap_provider_ns.route('/group_capacity_compliance_error', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class groupCapacityComplianceError(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.capacityprovider = kwargs['capacityprovider']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(GroupCapacityComplianceError)
    def post(self):
        """
        Describe me.
        Please.
        """
        self.capacityprovider.handleGroupCapacityComplianceError(
            cap_provider_ns.payload)
        return '', 204


@cap_provider_ns.route('/update_group_measurements', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class updateGroupMeasurements(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.capacityprovider = kwargs['capacityprovider']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(UpdateGroupMeasurements)
    def post(self):
        """
        Describe me.
        Please.
        """
        self.capacityprovider.handleUpdateGroupMeasurements(cap_provider_ns.payload)
        return '', 204
