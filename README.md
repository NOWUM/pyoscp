# pyOSCP

Python Rest-Interface for Open Smart Charging Protocol (OSCP) 2.0 built on Flask-RESTX, providing a OpenAPI interface.

OSCP is not as widely used as OCPI or OCPP which are much more a business standard.
It can be used to communicate flexibilities and capacities, having a typical negotiation process.

As version 1.x used a SOAP Approach, this can still be seen from the protocol.
The Registration between the participants uses a handshake and needs to have an open port on both sides.

To reduce reimplementation, an academic implementation is provided here, which furthermore allows to integrate with a new RESERVATIONS endpoint, if needed.

Currently, is no other public Python Implementation for the OSCProtocol.
The documentation of the protocol can be found here (https://www.openchargealliance.org/protocols/oscp-20/ - requires mail-registration)

## Install Instructions

`pip install pyoscp`

or after cloning the repository, one can run `pip install -e .` to work locally with the package.

## Package information

```
oscp
├── __init__.py
├── *_endpoints.py      # <- contains REST Endpoint Descriptions
├── json_models.py      # <- contains JSON Schemas in Flask-RestX
└── RegistrationManager # <- contains stubs which have to be inherited and implemented
```

## Configuration

`main.py` contains an example of how to use this project.
The managers are meant to be understood as interfaces, which must be implemented according to the business logic which is not part of this communications module.

An example architecture would use a background job to schedule answers (for example for the commands module) while saving the data from the post/patch requests in a seperate database, which is used for communication between the background job and the Flask app.