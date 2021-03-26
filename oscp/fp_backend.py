from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.models import GroupCapacityForecast, ForecastedBlock
import logging

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
flex_provider_ns = Namespace(name="fp", validate=True)

flex_provider_ns.models[GroupCapacityForecast.name] = GroupCapacityForecast
flex_provider_ns.models[ForecastedBlock.name] = ForecastedBlock

header_parser = flex_provider_ns.parser()
header_parser.add_argument('Authorization', required=True, location='headers')
header_parser.add_argument('X-Request-ID', required=True, location='headers')
header_parser.add_argument('X-Correlation-ID', location='headers')
header_parser.add_argument('X-Segment-Index', location='headers')
header_parser.add_argument('X-Segment-Count', location='headers')


@flex_provider_ns.route('/2.0/update_group_capacity_forecast',
                        doc={"description": "API Endpoint for Session management"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class updateGroupCapacityForecast(Resource):

    def __init__(self, api=None, *args, **kwargs):
        # forecastmanager is a black box dependency, which contains the logic
        self.forecastmanager = kwargs['forecastmanager']
        super().__init__(api, *args, **kwargs)

    @flex_provider_ns.expect(GroupCapacityForecast)
    @flex_provider_ns.marshal_with(GroupCapacityForecast)
    # @forecast_ns.response(204, 'No Content')
    def post(self):
        '''
        The message is sent from Capacity Provider to the Flexibility Provider and from Flexibility Provider to Capacity Optimizer which
        should generate an Optimum capacity forecast for the capacity that should be used in the specific group.
        '''

        self.forecastmanager.forecasts.append(flex_provider_ns.payload)
        # using logging instead of print is threadsafe and non-blocking
        # but you can't add multiple strings and expect that they get joined
        logging.info(str(self.forecastmanager.forecasts))
        return '', 204


@flex_provider_ns.route('/2.0/register', doc={"description": "API Endpoint for Registration of participants"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class register(Resource):
    def __init__(self):
        pass


@flex_provider_ns.route('/2.0/handshake', doc={"description": "API Endpoint for Registration of participants"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class handshake(Resource):
    def __init__(self):
        pass


@flex_provider_ns.route('/2.0/handshake_acknowledgement', doc={"description": "API Endpoint for Registration of participants"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class handshake_acknowledgement(Resource):
    def __init__(self):
        pass


@flex_provider_ns.route('/2.0/heartbeat', doc={"description": "API Endpoint for Registration of participants"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class heartbeat(Resource):
    def __init__(self):
        pass