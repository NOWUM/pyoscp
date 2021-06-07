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
from oscp.ep_endpoints import addPrice
from oscp.epc_endpoints import addForPriceCalculation


def createBlueprint(injected_objects, actor):
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
    if not actor in ['fp', 'cp', 'co', 'dso', 'ep', 'sch']:
        raise Exception('unknown actor')
    blueprint = Blueprint("api", __name__, url_prefix="/oscp")
    authorizations = {"Bearer": {"type": "apiKey",
                                 "in": "header",
                                 "name": "Authorization"}}

    api = Api(
        blueprint,
        version="2.0",
        title="OSCP OpenAPI Documentation",
        description="Welcome to the OpenAPI documentation site!",
        # the ui can be accessed from url_prefix+doc
        authorizations=authorizations,
        doc="/ui",
        default_label="Python OSCP Framework"
    )

    # inject objects through class kwargs
    # (small hack, must be done for new namespaces too)

    def addInjected(ns):
        for res in ns.resources:
            res.kwargs['resource_class_kwargs'] = injected_objects
        api.add_namespace(ns)

    # register namespace at api (must be done for new namespaces too)
    if actor == 'fp':
        addInjected(flex_provider_ns)
    elif actor == 'cp':
        addInjected(cap_provider_ns)
    elif actor == 'co':
        addInjected(cap_optimizer_ns)
    elif actor == 'dso':
        addPrice(cap_provider_ns)
        addInjected(cap_provider_ns)
    elif actor == 'ep':

        cap_provider_ns.name="ep"
        cap_provider_ns._path='/ep/2.0'
        addPrice(cap_provider_ns)
        addInjected(cap_provider_ns)
    elif actor == 'sch':
        addForPriceCalculation(flex_provider_ns)
        addInjected(flex_provider_ns)

    return blueprint