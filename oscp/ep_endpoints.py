from flask import request
from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from werkzeug.exceptions import Unauthorized
from oscp.registration import namespace_registration
from oscp.json_models import (create_header_parser, add_models_to_namespace,
                              ForecastedBlock, UpdateGroupLoadForecast,
                              GroupCapacityComplianceError, UpdateGroupMeasurements,
                              EnergyMeasurement)

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)

energy_provider_ns = Namespace(name="ep", validate=True, path="/ep/2.0")

models = [ForecastedBlock, UpdateGroupLoadForecast, UpdateGroupMeasurements,
          GroupCapacityComplianceError, EnergyMeasurement]

add_models_to_namespace(energy_provider_ns, models)
header_parser = create_header_parser(energy_provider_ns)
namespace_registration(energy_provider_ns)


@energy_provider_ns.route('/update_group_load_forecast', doc={"description": "API Endpoint for load profile?"})
@energy_provider_ns.expect(header_parser)  # validate=True
@energy_provider_ns.response(204, 'No Content')
@energy_provider_ns.response(404, 'Not found')
class updateGroupLoadForecast(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.energyprovider = kwargs['energyprovider']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @energy_provider_ns.expect(UpdateGroupLoadForecast)
    def post(self):
        """
        Describe me.
        Please.
        """
        if not self.registrationmanager.isRegistered(request.headers['Authorization']):
            raise Unauthorized('Not authorized.')
        self.energyprovider.handleUpdateGroupLoadForecast(
            energy_provider_ns.payload)
        return '', 204