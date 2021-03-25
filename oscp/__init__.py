#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 18:02:46 2021

@author: maurer

Api definition file
"""

from flask import Blueprint
from flask_restx import Api

from oscp.forecasts import forecast_ns


def createBlueprint(injected_objects):
    '''
    Creates API blueprint with injected Objects.
    Must contain a forecastmanager and others...

    Parameters
    ----------
    injected_objects : TYPE
        DESCRIPTION.

    Returns
    -------
    blueprint

    '''
    blueprint = Blueprint("api", __name__, url_prefix="/oscp/fp/2.0")
    authorizations = {"Bearer": {"type": "apiKey",
                                 "in": "header", "name": "Authorization"}}

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
    for namesp in [forecast_ns]:
        for res in namesp.resources:
            res.kwargs['resource_class_kwargs'] = injected_objects
            
    # register namespace at api (must be done for new namespaces too)
    api.add_namespace(forecast_ns)  # , path="/"+namesp.name)
    return blueprint
