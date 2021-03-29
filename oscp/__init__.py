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
from oscp.fp_endpoints import flex_provider_ns
from oscp.cp_endpoints import cap_provider_ns
from oscp.co_endpoints import cap_optimizer_ns


def createBlueprint(injected_objects, actors=['fp','cp','co']):
    """
    Creates API blueprint with injected Objects.
    Must contain a forecastmanager and others...

    Parameters
    ----------
    :param injected_objects: Irgendwie werden hier wohl Klassen/Module/Funktionen übergeben zB endpointmanager
    :param actor: 'cp', 'fp', 'co' for Capacity Provider, Flexibility Provider and Capacity Optimizer

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
        doc="/ui",
        authorizations=authorizations,
        default_label="Python OSCP Framework"
    )

    # inject objects through class kwargs
    # (small hack, must be done for new namespaces too)
    for ns in [flex_provider_ns, cap_provider_ns, cap_optimizer_ns]:
        for res in ns.resources:
            res.kwargs['resource_class_kwargs'] = injected_objects

    # register namespace at api (must be done for new namespaces too)
    if  'fp' in actors:
        api.add_namespace(flex_provider_ns)  # , path="/"+namesp.name)

    if  'cp' in actors:
        api.add_namespace(cap_provider_ns)

    if  'co' in actors:
        api.add_namespace(cap_optimizer_ns)

    return blueprint
