#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 18:02:46 2021

@author: maurer

Api definition file
"""
from flask import Blueprint
from flask_restx import Api

# from oscp.forecasts import forecast_ns
from pyoscp.oscp.fp_endpoints import flex_provider_ns
from pyoscp.oscp.cp_endpoints import cap_provider_ns
from pyoscp.oscp.co_endpoints import cap_optimizer_ns
#from oscp.ep_endpoints import energy_provider_ns
from pyoscp.oscp.ep_endpoints import energy_provider_ns


def createBlueprint(injected_objects, actors=['fp', 'cp', 'co', 'ep']):
    """
    Creates API blueprint with injected Objects.
    Must contain a forecastmanager and others...

    Parameters
    ----------
    :param injected_objects: Providing endpoint managers
    :param actors: 'cp', 'fp', 'co' for Capacity Provider, Flexibility Provider and Capacity Optimizer

    Returns
    -------
    :return blueprint: Blueprint dies das

    """
    blueprint = Blueprint("api", __name__, url_prefix="/oscp")
    authorizations = {"Bearer": {"type": "apiKey",
                                 "in": "header",
                                 "name": "Authorization"}}

    api = Api(
        blueprint,
        version="1.0",
        title="OSCP OpenAPI Documentation",
        description="Welcome to the OpenAPI documentation site!",
        # the ui can be accessed from url_prefix+doc
        authorizations=authorizations,
        doc="/ui",
        default_label="Python OSCP Framework"
    )

    # inject objects through class kwargs
    # (small hack, must be done for new namespaces too)
    for ns in [flex_provider_ns, cap_provider_ns, cap_optimizer_ns, energy_provider_ns]:
        for res in ns.resources:
            res.kwargs['resource_class_kwargs'] = injected_objects

    # register namespace at api (must be done for new namespaces too)
    if 'fp' in actors:
        api.add_namespace(flex_provider_ns)

    if 'cp' in actors:
        api.add_namespace(cap_provider_ns)

    if 'co' in actors:
        api.add_namespace(cap_optimizer_ns)

    if 'ep' in actors:
        api.add_namespace(energy_provider_ns)

    return blueprint