#!/usr/bin/python
# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Module Name : power recording API
#               request YOKOGAWA Powermeter with redfish
# Version : 1.0
#
# Copyright © 2018 Orange
# This software is distributed under the Apache 2 license
# <http://www.apache.org/licenses/LICENSE-2.0.html>
#
# -------------------------------------------------------
#
# Created     : 2018-10
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     API monitoring
# -------------------------------------------------------
# History     :
# 1.0.0 - 2018-10-16 : Release of the file
#
"""Yoko to redfish main code."""
import logging.config
import sys
import flask_restplus.apidoc
import yaml

from flask import Flask, Blueprint
import settings
from api.endpoints.chassis import NS as chassis_namespace
from api.restplus import API as api

APP = Flask(__name__)

logging.config.fileConfig('conf/webapp-logging.conf')
LOG = logging.getLogger(__name__)
CONFIG = None


def configure_app(flask_app):
    """Load application configuration to flask.

    Load configuration to Flask object
        :param flask_app: Flask application to configure
        :type flask_app: Flask
    """
    flask_app.config[
        'SWAGGER_UI_DOC_EXPANSION'
    ] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION

    flask_app.config[
        'RESTPLUS_VALIDATE'
    ] = settings.RESTPLUS_VALIDATE

    flask_app.config[
        'RESTPLUS_MASK_SWAGGER'
    ] = settings.RESTPLUS_MASK_SWAGGER

    flask_app.config[
        'ERROR_404_HELP'
    ] = settings.RESTPLUS_ERROR_404_HELP

    flask_app.config[
        'APPLICATION_ROOT'
    ] = settings.API["context_root"]


def initialize_app(flask_app):
    """Apply application configuration.

    Load configuration to Flask object and apply configuration to it
        :param flask_app: Flask application to configure
        :type flask_app: Flask
    """
    configure_app(flask_app)

    blueprint = Blueprint('api', __name__,
                          url_prefix=settings.API["context_root"])
    api.init_app(blueprint)

    api.add_namespace(chassis_namespace)

    api_doc = flask_restplus.apidoc.apidoc
    api_doc.url_prefix = settings.API["context_root"] + "/doc"
    flask_app.register_blueprint(blueprint)


@APP.after_request
def after_request(response):
    """Add CORS Headers."""
    response.headers.add('Access-Control-Allow-Origin',
                         '*')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE')
    return response


def main():
    """Application launcher."""
    server_binding = settings.BIND.split(':')
    APP.run(
        debug=settings.FLASK_DEBUG,
        port=int(server_binding[1]),
        host=server_binding[0],
        threaded=True
    )


def load_config():
    """Load application config from YAML."""
    LOG.info("Server power consumption daemon is starting")
    with open("conf/webapp-settings.yaml", 'r') as stream:
        try:
            config = yaml.load(stream)
            settings.BIND = config["BIND"]
            settings.POWERMETERS = config["POWERMETERS"]
            settings.YOKOTOOL_PATH = config["YOKOTOOL_PATH"]
        except yaml.YAMLError:
            LOG.exception("Error while loading config")
            sys.exit()
    initialize_app(APP)
    LOG.info('>>>>> Starting server  <<<<<')


load_config()
if __name__ == "__main__":
    main()
