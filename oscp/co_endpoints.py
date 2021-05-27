from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.json_models import (add_models_to_namespace, create_header_parser,
                              GroupCapacityForecast, ForecastedBlock)
from oscp.registration import namespace_registration

cap_optimizer_ns = Namespace(name="co", validate=True, path="/co/2.0")

models = [GroupCapacityForecast, ForecastedBlock]

add_models_to_namespace(cap_optimizer_ns, models)
header_parser = create_header_parser(cap_optimizer_ns)
namespace_registration(cap_optimizer_ns)


@cap_optimizer_ns.route('/update_group_capacity_forecast', doc={"description": "API Endpoint for Session management"})
@cap_optimizer_ns.expect(header_parser)  # validate=True
@cap_optimizer_ns.response(204, 'No Content')
class updateGroupCapacityForecast(Resource):

    def __init__(self, api=None, *args, **kwargs):
        self.capacityoptimizer = kwargs['capacityoptimizer']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @cap_optimizer_ns.expect(GroupCapacityForecast)
    # @forecast_ns.response(204, 'No Content')
    def post(self):
        """
        The message is sent from Capacity Provider to the Flexibility Provider and from Flexibility Provider to Capacity Optimizer which
        should generate an Optimum capacity forecast for the capacity that should be used in the specific group.
        """

        self.capacityoptimizer.handleUpdateGroupCapacityForecast(
            cap_optimizer_ns.payload)
        return '', 204


@cap_optimizer_ns.route('/update_asset_measurements', doc={"description": "API Endpoint for Session management"})
@cap_optimizer_ns.expect(header_parser)  # validate=True
@cap_optimizer_ns.response(204, 'No Content')
class updateAssetMeasurements(Resource):

    def __init__(self, api=None, *args, **kwargs):
        self.capacityoptimizer = kwargs['capacityoptimizer']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @cap_optimizer_ns.expect(GroupCapacityForecast)
    def post(self):
        self.registrationmanager._check_access_token()
        self.capacityoptimizer.handleUpdateAssetMeasurements(
            cap_optimizer_ns.payload)
        return '', 204