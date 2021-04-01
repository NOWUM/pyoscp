from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.json_models import ForecastedBlock, Register, VersionUrl, Heartbeat, HandshakeAcknowledgement, \
    AdjustGroupCapacityForecast, GroupCapacityComplianceError, UpdateGroupMeasurements, Measurements, \
    RequiredBehaviour
import logging

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
cap_provider_ns = Namespace(name="cp", validate=True)
cap_provider_ns.models[ForecastedBlock.name] = ForecastedBlock
cap_provider_ns.models[Register.name] = Register
cap_provider_ns.models[VersionUrl.name] = VersionUrl
cap_provider_ns.models[Heartbeat.name] = Heartbeat
cap_provider_ns.models[HandshakeAcknowledgement.name] = HandshakeAcknowledgement
cap_provider_ns.models[AdjustGroupCapacityForecast.name] = AdjustGroupCapacityForecast
cap_provider_ns.models[GroupCapacityComplianceError.name] = GroupCapacityComplianceError
cap_provider_ns.models[UpdateGroupMeasurements.name] = UpdateGroupMeasurements
cap_provider_ns.models[Measurements.name] = Measurements
cap_provider_ns.models[RequiredBehaviour.name] = RequiredBehaviour

header_parser = cap_provider_ns.parser()
header_parser.add_argument('Authorization', required=True, location='headers')
header_parser.add_argument('X-Request-ID', required=True, location='headers')
header_parser.add_argument('X-Correlation-ID', location='headers')
header_parser.add_argument('X-Segment-Index', location='headers')
header_parser.add_argument('X-Segment-Count', location='headers')


@cap_provider_ns.route('/2.0/register', doc={"description": "API Endpoint for Registration of participants"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class register(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.endpointmanager = kwargs['endpointmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(Register)
    @cap_provider_ns.marshal_with(Register)
    def post(self):
        """
        Registering endpoints is needed in order to make sure the received messages on these endpoints actually come from the designated party(UND DAS HIER?!)

        For instance as a Flexibility Provider I want to make sure the Capacity Forecast (that can potentially have a negative influence on the experience of my customers) actually comes from my trusted Capacity Provider.
        To register one party to another, every party must create a unique token to use for authentication. This token will have to be sent from one party to the other in a secure way that is outside the scope of this protocol. Every endpoint ought to be registered using a token.

        The (one-time) registration of an endpoint MUST be done prior to sending handshakes which is described below.
        """

        self.endpointmanager.addEndpoint(cap_provider_ns.payload)
        # using logging instead of print is threadsafe and non-blocking
        # but you can't add multiple strings and expect that they get joined
        logging.info('Log doch mal was')
        return '', 204


@cap_provider_ns.route('/2.0/handshake_acknowledgement', doc={"description": "API Endpoint for Handshake management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class handshake_acknowledgement(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.endpointmanager = kwargs['endpointmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(HandshakeAcknowledgement)
    def post(self):
        """
        Describe me.
        Please.
        """

        return '', 204


@cap_provider_ns.route('/2.0/heartbeat', doc={"description": "API Endpoint for Registration of participants"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class heartbeat(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.endpointmanager = kwargs['endpointmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(Heartbeat)
    def post(self):
        """
        Describe me.
        Please.
        """

        return '', 204


@cap_provider_ns.route('/2.0/adjust_group_capacity_forecast', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class adjustGroupCapacityForecast(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.forecastmanager = kwargs['forecastmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(AdjustGroupCapacityForecast)
    def post(self):
        """
        Describe me.
        Please.
        """

        return '', 204


@cap_provider_ns.route('/2.0/group_capacity_compliance_error', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class groupCapacityComplianceError(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.forecastmanager = kwargs['forecastmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(GroupCapacityComplianceError)
    def post(self):
        """
        Describe me.
        Please.
        """

        return '', 204


@cap_provider_ns.route('/2.0/update_group_measurements', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class updateGroupMeasurements(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.forecastmanager = kwargs['forecastmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(UpdateGroupMeasurements)
    def post(self):
        """
        Describe me.
        Please.
        """

        return '', 204