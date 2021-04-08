from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.json_models import GroupCapacityForecast, ForecastedBlock
import logging

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
cap_optimizer_ns = Namespace(name="co", validate=True)

cap_optimizer_ns.models[GroupCapacityForecast.name] = GroupCapacityForecast
cap_optimizer_ns.models[ForecastedBlock.name] = ForecastedBlock

header_parser = cap_optimizer_ns.parser()
header_parser.add_argument('Authorization', required=True, location='headers')
header_parser.add_argument('X-Request-ID', required=True, location='headers')
header_parser.add_argument('X-Correlation-ID', location='headers')
header_parser.add_argument('X-Segment-Index', location='headers')
header_parser.add_argument('X-Segment-Count', location='headers')


@cap_optimizer_ns.route('/2.0/register', doc={"description": "API Endpoint for Registration of participants"})
@cap_optimizer_ns.expect(header_parser)  # validate=True
@cap_optimizer_ns.response(204, 'No Content')
class register(Resource):
    def __init__(self):
        pass


@cap_optimizer_ns.route('/2.0/handshake', doc={"description": "API Endpoint for Registration of participants"})
@cap_optimizer_ns.expect(header_parser)  # validate=True
@cap_optimizer_ns.response(204, 'No Content')
class handshake(Resource):
    def __init__(self):
        pass


@cap_optimizer_ns.route('/2.0/heartbeat', doc={"description": "API Endpoint for Registration of participants"})
@cap_optimizer_ns.expect(header_parser)  # validate=True
@cap_optimizer_ns.response(204, 'No Content')
class heartbeat(Resource):
    def __init__(self):
        pass


@cap_optimizer_ns.route('/2.0/update_group_capacity_forecast', doc={"description": "API Endpoint for Session management"})
@cap_optimizer_ns.expect(header_parser)  # validate=True
@cap_optimizer_ns.response(204, 'No Content')
class updateGroupCapacityForecast(Resource):

    def __init__(self, api=None, *args, **kwargs):
        self.capacityoptimizer = kwargs['capacityoptimizer']
        super().__init__(api, *args, **kwargs)

    @cap_optimizer_ns.expect(GroupCapacityForecast)
    @cap_optimizer_ns.marshal_with(GroupCapacityForecast)
    # @forecast_ns.response(204, 'No Content')
    def post(self):
        """
        The message is sent from Capacity Provider to the Flexibility Provider and from Flexibility Provider to Capacity Optimizer which
        should generate an Optimum capacity forecast for the capacity that should be used in the specific group.
        """

        self.capacityoptimizer.handleUpdateGroupCapacityForecast(
            cap_optimizer_ns.payload)
        return '', 204


@cap_optimizer_ns.route('/2.0/update_asset_measurements', doc={"description": "API Endpoint for Session management"})
@cap_optimizer_ns.expect(header_parser)  # validate=True
@cap_optimizer_ns.response(204, 'No Content')
class updateAssetMeasurements(Resource):

    def __init__(self, api=None, *args, **kwargs):
        self.capacityoptimizer = kwargs['capacityoptimizer']
        super().__init__(api, *args, **kwargs)

    @cap_optimizer_ns.expect(GroupCapacityForecast)
    @cap_optimizer_ns.marshal_with(GroupCapacityForecast)
    def post(self):

        self.capacityoptimizer.handleUpdateAssetMeasurements(
            cap_optimizer_ns.payload)
        return '', 204