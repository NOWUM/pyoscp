from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.json_models import (create_header_parser, add_models_to_namespace,
                              GroupCapacityForecast, ForecastedBlock, Register,
                              VersionUrl, Handshake, HandshakeAcknowledgement,
                              Heartbeat, RequiredBehaviour)
import logging

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
flex_provider_ns = Namespace(name="fp", validate=True)

models = [GroupCapacityForecast, ForecastedBlock, Register, VersionUrl,
          Handshake, HandshakeAcknowledgement, Heartbeat, RequiredBehaviour]

add_models_to_namespace(flex_provider_ns, models)

header_parser = create_header_parser(flex_provider_ns)


@flex_provider_ns.route('/2.0/register',
                        doc={"description": "API Endpoint for Registration of participants.(WIESO STEHT DAS HIER?)\n"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class register(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.endpointmanager = kwargs['endpointmanager']
        super().__init__(api, *args, **kwargs)

    @flex_provider_ns.expect(Register)
    @flex_provider_ns.marshal_with(Register)
    def post(self):
        """
        Registering endpoints is needed in order to make sure the received messages on these endpoints actually come from the designated party(UND DAS HIER?!)

        For instance as a Flexibility Provider I want to make sure the Capacity Forecast (that can potentially have a negative influence on the experience of my customers) actually comes from my trusted Capacity Provider.
        To register one party to another, every party must create a unique token to use for authentication. This token will have to be sent from one party to the other in a secure way that is outside the scope of this protocol. Every endpoint ought to be registered using a token.

        The (one-time) registration of an endpoint MUST be done prior to sending handshakes which is described below.
        """

        self.endpointmanager.registerEndpoint(reg=flex_provider_ns.payload)
        logging.info('Log something, please.')
        return '', 204


@flex_provider_ns.route('/2.0/handshake', doc={"description": "API Endpoint for Handshake management"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class handshake(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.endpointmanager = kwargs['endpointmanager']
        super().__init__(api, *args, **kwargs)

    @flex_provider_ns.expect(Handshake)
    def post(self):
        """
        Description for the overview here.

        1. The CP sends a Handshake message to the FP.
        2. The FP accepts the handshake by replying with a HTTP 204 and sending a HandshakeAcknowledge message to the CP.
        3. The CP accepts the handshake acknowledge by replying with a HTTP 204.
        """

        return '', 204


@flex_provider_ns.route('/2.0/handshake_acknowledgement', doc={"description": "API Endpoint for Handshake management"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class handshake_acknowledgement(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.endpointmanager = kwargs['endpointmanager']
        super().__init__(api, *args, **kwargs)

    @flex_provider_ns.expect(HandshakeAcknowledgement)
    def post(self):
        """
        Description for the overview here.

        1. The CP sends a Handshake message to the FP.
        2. The FP accepts the handshake by replying with a HTTP 204 and sending a HandshakeAcknowledge message to the CP.
        3. The CP accepts the handshake acknowledge by replying with a HTTP 204.
        """

        return '', 204


@flex_provider_ns.route('/2.0/heartbeat', doc={"description": "API Endpoint for Heartbeat management"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class heartbeat(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.endpointmanager = kwargs['endpointmanager']
        super().__init__(api, *args, **kwargs)

    @flex_provider_ns.expect(Heartbeat)
    def post(self):
        """
        Describe me.
        Please.
        """

        return '', 204


@flex_provider_ns.route('/2.0/update_group_capacity_forecast',
                        doc={"description": "API Endpoint for Session management"})
@flex_provider_ns.expect(header_parser)  # validate=True
@flex_provider_ns.response(204, 'No Content')
class updateGroupCapacityForecast(Resource):

    def __init__(self, api=None, *args, **kwargs):
        # forecastmanager is a black box dependency, which contains the logic
        self.flexibilityprovider = kwargs['flexibilityprovider']
        super().__init__(api, *args, **kwargs)

    @flex_provider_ns.expect(GroupCapacityForecast)
    @flex_provider_ns.marshal_with(GroupCapacityForecast)
    # @forecast_ns.response(204, 'No Content')
    def post(self):
        """
        The message is sent from Capacity Provider to the Flexibility Provider and from Flexibility Provider to Capacity Optimizer which
        should generate an Optimum capacity forecast for the capacity that should be used in the specific group.
        """

        self.flexibilityprovider.handleUpdateGroupCapacityForecast(
            flex_provider_ns.payload)
        return '', 204