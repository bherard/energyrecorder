# -*- coding: utf-8 -*-
"""Recorder API app main code."""
# --------------------------------------------------------
# Module Name : terraHouat power recording API
# Version : 1.0
#
# Software Name : Open NFV functest
# Version :
#
# Copyright © 2017 Orange
# This software is distributed under the Apache 2 license
# <http://www.apache.org/licenses/LICENSE-2.0.html>
#
# -------------------------------------------------------
# File Name   : terrhouat/app.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Main app
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
#
import logging.config
import sys

import flask_restplus.apidoc
import requests
import yaml
from flask import Blueprint, Flask

import settings
from api.endpoints.monitoring import NS as monitoring_namespace
from api.endpoints.recorder import NS as recorder_namespace
from api.endpoints.servers import NS as servers_namespace
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

    api.add_namespace(servers_namespace)
    api.add_namespace(recorder_namespace)
    api.add_namespace(monitoring_namespace)

    api_doc = flask_restplus.apidoc.apidoc
    api_doc.url_prefix = settings.API["context_root"] + "/doc"
    flask_app.register_blueprint(blueprint)
    requests.urllib3.disable_warnings()


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
    APP.run(debug=settings.FLASK_DEBUG,
            port=int(server_binding[1]),
            host=server_binding[0])


def load_config():
    """Load application config from YAML."""
    LOG.info("Server power consumption daemon is starting")
    with open("conf/webapp-settings.yaml", 'r') as stream:
        try:
            config = yaml.load(stream)
            settings.BIND = config["BIND"]
            settings.INFLUX = config["INFLUX"]
            if "ALWAYS_RECORD" in config:
                settings.ALWAYS_RECORD = config["ALWAYS_RECORD"]
        except yaml.YAMLError:
            LOG.exception("Error while loading config")
            sys.exit()
    initialize_app(APP)
    LOG.info('>>>>> Starting server  <<<<<')


load_config()
if __name__ == "__main__":
    main()
