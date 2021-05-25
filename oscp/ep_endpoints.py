from flask_restx import Resource, Namespace
from oscp.registration import namespace_registration
from oscp.json_models import create_header_parser, add_models_to_namespace
from oscp.ep_models import ExtForecastedBlock, UpdateGroupLoadForecast

energy_provider_ns = Namespace(name="ep", validate=True, path="/ep/2.0")

models = [ExtForecastedBlock, UpdateGroupLoadForecast]

add_models_to_namespace(energy_provider_ns, models)
header_parser = create_header_parser(energy_provider_ns)
namespace_registration(energy_provider_ns)


@energy_provider_ns.route('/update_group_load_forecast')
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
        Update Load TimeSeries which can contain a Load or a Price (or both).
        Can be used by a EnergyProvider or a DSO to communicate a price series
        """
        token = self.registrationmanager._check_access_token()
        self.energyprovider.handleUpdateGroupLoadForecast(
            energy_provider_ns.payload, token)
        return '', 204