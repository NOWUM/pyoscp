#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 11 19:19:30 2021

@author: maurer
"""

from flask_restx import Resource
from oscp.json_models import (add_models_to_namespace, create_header_parser,
                              Register, Handshake, HandshakeAcknowledgement, Heartbeat, VersionUrl, RequiredBehaviour)


def namespace_registration(namespace):
    add_models_to_namespace(namespace, [
        Register, Handshake, HandshakeAcknowledgement, Heartbeat, VersionUrl, RequiredBehaviour])
    header_parser = create_header_parser(namespace)

    @namespace.route('/register', doc={"description": "API Endpoint for Registration of participants"})
    @namespace.expect(header_parser)  # validate=True
    @namespace.response(204, 'No Content')
    class register(Resource):
        def __init__(self, api=None, *args, **kwargs):
            self.registrationmanager = kwargs['registrationmanager']
            super().__init__(api, *args, **kwargs)

        @namespace.expect(Register)
        def post(self):
            """
            Registering endpoints is needed in order to make sure the received messages on these endpoints actually come from the designated party(UND DAS HIER?!)

            For instance as a Flexibility Provider I want to make sure the Capacity Forecast (that can potentially have a negative influence on the experience of my customers) actually comes from my trusted Capacity Provider.
            To register one party to another, every party must create a unique token to use for authentication. This token will have to be sent from one party to the other in a secure way that is outside the scope of this protocol. Every endpoint ought to be registered using a token.

            The (one-time) registration of an endpoint MUST be done prior to sending handshakes which is described below.
            """
            self.registrationmanager.handleRegister(namespace.payload)
            return '', 204

        @namespace.expect(Register)
        def put(self):
            self.registrationmanager.updateEndpoint(namespace.payload)
            return '', 204

        def delete(self):
            self.registrationmanager.unregister()
            return '', 204

    @namespace.route('/handshake', doc={"description": "API Endpoint for Handshake of participants"})
    @namespace.expect(header_parser)  # validate=True
    @namespace.response(204, 'No Content')
    class handshake(Resource):
        def __init__(self, api=None, *args, **kwargs):
            self.registrationmanager = kwargs['registrationmanager']
            super().__init__(api, *args, **kwargs)

        @namespace.expect(Handshake)
        def post(self):
            """
            Send a handshake message

            1. The CP sends a Handshake message to the FP.
            2. The FP accepts the handshake by replying with a HTTP 204 and sending a HandshakeAcknowledge message to the CP.
            3. The CP accepts the handshake acknowledge by replying with a HTTP 204.
            """
            self.registrationmanager.handleHandshake(namespace.payload)
            return '', 204

    @namespace.route('/handshake_acknowledgment',
                     doc={"description": "API Endpoint for Handshake aknowledgement of participants"})
    @namespace.expect(header_parser)  # validate=True
    @namespace.response(204, 'No Content')
    class handshake_acknowledgement(Resource):
        def __init__(self, api=None, *args, **kwargs):
            self.registrationmanager = kwargs['registrationmanager']
            super().__init__(api, *args, **kwargs)

        @namespace.expect(HandshakeAcknowledgement)
        def post(self):
            """
            Acknowledges a handshake message

            1. The CP sends a Handshake message to the FP.
            2. The FP accepts the handshake by replying with a HTTP 204 and sending a HandshakeAcknowledge message to the CP.
            3. The CP accepts the handshake acknowledge by replying with a HTTP 204.
            """
            self.registrationmanager.handleHandshakeAck(namespace.payload)
            return '', 204

    @namespace.route('/heartbeat', doc={"description": "API Endpoint for Registration of participants"})
    @namespace.expect(header_parser)  # validate=True
    @namespace.response(204, 'No Content')
    class heartbeat(Resource):
        def __init__(self, api=None, *args, **kwargs):
            self.registrationmanager = kwargs['registrationmanager']
            super().__init__(api, *args, **kwargs)

        @namespace.expect(Heartbeat)
        def post(self):
            """
            Send a heartbeat message

            """
            self.registrationmanager.handleHeartbeat(namespace.payload)
            return '', 204