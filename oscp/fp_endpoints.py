from oscp.registration import namespace_registration
from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.json_models import (create_header_parser, add_models_to_namespace,
                              GroupCapacityForecast, ForecastedBlock)

flex_provider_ns = Namespace(name="fp", validate=True, path="/fp/2.0")

models = [GroupCapacityForecast, ForecastedBlock]

add_models_to_namespace(flex_provider_ns, models)

header_parser = create_header_parser(flex_provider_ns)
namespace_registration(flex_provider_ns)


@flex_provider_ns.route('/update_group_capacity_forecast',
                        doc={"description": "API Endpoint for Session management"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class updateGroupCapacityForecast(Resource):

    def __init__(self, api=None, *args, **kwargs):
        # forecastmanager is a black box dependency, which contains the logic
        self.flexibilityprovider = kwargs['flexibilityprovider']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @flex_provider_ns.expect(GroupCapacityForecast)
    @flex_provider_ns.marshal_with(GroupCapacityForecast)
    # @forecast_ns.response(204, 'No Content')
    def post(self):
        """
        The message is sent from Capacity Provider to the Flexibility Provider and from Flexibility Provider to Capacity Optimizer which
        should generate an Optimum capacity forecast for the capacity that should be used in the specific group.
        """
        token = self.registrationmanager._check_access_token()
        self.flexibilityprovider.handleUpdateGroupCapacityForecast(
            flex_provider_ns.payload, token)
        return '', 204