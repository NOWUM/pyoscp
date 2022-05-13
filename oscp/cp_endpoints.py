from flask_restx import Resource, Namespace  # ,add_models_to__namespace
from oscp.registration import namespace_registration
from oscp.json_models import (create_header_parser, add_models_to_namespace,
                              ForecastedBlock, GroupCapacityForecast,
                              GroupCapacityComplianceError, UpdateGroupMeasurements,
                              EnergyMeasurement)

# a namespace is a group of api routes which have the same prefix
# (i think mostly all are in the same namespace in oscp)
cap_provider_ns = Namespace(name="cp", validate=True, path="/cp/2.0")

models = [ForecastedBlock, GroupCapacityForecast, UpdateGroupMeasurements,
          GroupCapacityComplianceError, EnergyMeasurement]

add_models_to_namespace(cap_provider_ns, models)
header_parser = create_header_parser(cap_provider_ns)
namespace_registration(cap_provider_ns)


@cap_provider_ns.route('/adjust_group_capacity_forecast', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content!!!')
@cap_provider_ns.response(404, 'Not found!')
class adjustGroupCapacityForecast(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.capacityprovider = kwargs['capacityprovider']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(GroupCapacityForecast)
    def post(self):
        """
        Demands do not match the capacity limits

        In case the demands of a Flexibility Provider do not match the capacity limits set by the Capacity Provider,
        it is possible for the Flexibility Provider to request for adjustment of the capacity.

        If the Capacity Provider in fact decides to respond to the request it will report the updated Capacity Forecast
        within a UpdateGroupCapacityForecast message.
        """
        token = self.registrationmanager._check_access_token()
        self.capacityprovider.handleAdjustGroupCapacityForecast(
            cap_provider_ns.payload, token)
        return '', 204


@cap_provider_ns.route('/group_capacity_compliance_error', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class groupCapacityComplianceError(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.capacityprovider = kwargs['capacityprovider']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(GroupCapacityComplianceError)
    def post(self):
        """
        FP can not comply to the Capacity Forecast

        This message is for notifying the Capacity Provider the Flexibility Provider cannot comply to the Capacity Forecast within an UpdateGroupCapacityForecast message.

        The Capacity Forecast referred to by the Flexibility Provider SHALL be indicated by the X-Correlation-ID header.
        """
        token = self.registrationmanager._check_access_token()
        self.capacityprovider.handleGroupCapacityComplianceError(
            cap_provider_ns.payload, token)
        return '', 204


@cap_provider_ns.route('/update_group_measurements', doc={"description": "API Endpoint for capacity management"})
@cap_provider_ns.expect(header_parser)  # validate=True
@cap_provider_ns.response(204, 'No Content')
class updateGroupMeasurements(Resource):
    def __init__(self, api=None, *args, **kwargs):
        self.capacityprovider = kwargs['capacityprovider']
        self.registrationmanager = kwargs['registrationmanager']
        super().__init__(api, *args, **kwargs)

    @cap_provider_ns.expect(UpdateGroupMeasurements)
    def post(self):
        """
        Updating aggregated group measurements

        This message is for communicating the total usage per aggregated area (group) from Flexibility Provider back to the Capacity Provider.

        This information is necessary for the Capacity Provider to know how much energy each Flexibility Provider has used according to the Capacity Forecast limits sent within the UpdateGroupCapacityForecast message.
        Furthermore, the information can be used to determine a division of the Capacity Forecast over the different Flexibility Providers.
        The total usage can be 'nothing'. Therefore, the measurements field can be empty.
        """
        token = self.registrationmanager._check_access_token()
        self.capacityprovider.handleUpdateGroupMeasurements(
            cap_provider_ns.payload, token)
        return '', 204
