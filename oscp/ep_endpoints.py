from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.registration import namespace_registration
from oscp.json_models import (create_header_parser, add_models_to_namespace,
                              ForecastedBlock, AdjustGroupCapacityForecast,
                              GroupCapacityComplianceError, UpdateGroupMeasurements,
                              EnergyMeasurement)

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
energy_provider_ns = Namespace(name="ep", validate=True, path="/ep/2.0")

models = [ForecastedBlock, AdjustGroupCapacityForecast, UpdateGroupMeasurements,
          GroupCapacityComplianceError, EnergyMeasurement]

add_models_to_namespace(energy_provider_ns, models)
header_parser = create_header_parser(energy_provider_ns)
namespace_registration(energy_provider_ns)


@energy_provider_ns.route('/update_group_capacity_forecast', doc={"description": "API Endpoint for load profile?"})
@energy_provider_ns.expect(header_parser)  # validate=True
@energy_provider_ns.response(204, 'No Content!!!')
@energy_provider_ns.response(404, 'Not found!')
class adjustGroupCapacityForecast(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.capacityprovider = kwargs['energyprovider']
        super().__init__(api, *args, **kwargs)

    @energy_provider_ns.expect(AdjustGroupCapacityForecast)
    def post(self):
        """
        Describe me.
        Please.
        """
        self.capacityprovider.handleUpdateGroupCapacityForecast(
            energy_provider_ns.payload)
        return '', 204