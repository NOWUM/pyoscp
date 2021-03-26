from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.models import GroupCapacityForecast, ForecastedBlock
import logging

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
cap_provider_ns = Namespace(name="cp", validate=True)

cap_provider_ns.models[ForecastedBlock.name] = ForecastedBlock

header_parser = cap_provider_ns.parser()
header_parser.add_argument('Authorization', required=True, location='headers')
header_parser.add_argument('X-Request-ID', required=True, location='headers')
header_parser.add_argument('X-Correlation-ID', location='headers')
header_parser.add_argument('X-Segment-Index', location='headers')
header_parser.add_argument('X-Segment-Count', location='headers')


@cap_provider_ns.route('/register', doc={"description": "API Endpoint for Registration of participants"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class register(Resource):
    def __init__(self):
        pass


@cap_provider_ns.route('/2.0/handshake_acknowledgement', doc={"description": "API Endpoint for Registration of participants"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class handshake_acknowledgement(Resource):
    def __init__(self):
        pass


@cap_provider_ns.route('/2.0/heartbeat', doc={"description": "API Endpoint for Registration of participants"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class heartbeat(Resource):
    def __init__(self):
        pass


@cap_provider_ns.route('/2.0/adjust_group_capacity_forecast', doc={"description": "API Endpoint for Session management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class adjustGroupCapacityForecast(Resource):

    def __init__(self, api=None, *args, **kwargs):
        self.this = None
        self.that = None


@cap_provider_ns.route('/2.0/group_capacity_compliance_error', doc={"description": "API Endpoint for Session management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class groupCapacityComplianceError(Resource):

    def __init__(self, api=None, *args, **kwargs):
        self.this = None
        self.that = None


@cap_provider_ns.route('/2.0/update_group_measurements', doc={"description": "API Endpoint for Session management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class updateGroupMeasurements(Resource):

    def __init__(self, api=None, *args, **kwargs):
        self.this = None
        self.that = None