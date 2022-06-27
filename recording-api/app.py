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

import flask_restx.apidoc
import requests
import yaml
from flask import Blueprint, Flask

import settings
from api.endpoints.monitoring import NS as monitoring_namespace
from api.endpoints.recorder import NS as recorder_namespace
#from api.endpoints.servers import NS as servers_namespace
from api.endpoints.equipements import NS as equipements_namespace
from api.restx import API as api

APP = Flask(__name__)

logging.config.fileConfig('conf/webapp-logging.conf')
LOG = logging.getLogger(__name__)
CONFIG = None


class ProxyFix():

    """This middleware can be applied to add HTTP proxy support to an
    application that was not designed with HTTP proxies in mind.  It
    sets `REMOTE_ADDR`, `HTTP_HOST` from `X-Forwarded` headers.  While
    Werkzeug-based applications already can use
    :py:func:`werkzeug.wsgi.get_host` to retrieve the current host even if
    behind proxy setups, this middleware can be used for applications which
    access the WSGI environment directly.

    If you have more than one proxy server in front of your app, set
    `num_proxies` accordingly.

    Do not use this middleware in non-proxy setups for security reasons.

    The original values of `REMOTE_ADDR` and `HTTP_HOST` are stored in
    the WSGI environment as `werkzeug.proxy_fix.orig_remote_addr` and
    `werkzeug.proxy_fix.orig_http_host`.

    :param app: the WSGI application
    :param num_proxies: the number of proxy servers in front of the app.
    """

    def __init__(self, app, num_proxies=1):
        self.app = app
        self.num_proxies = num_proxies

    def get_remote_addr(self, forwarded_for):
        """Selects the new remote addr from the given list of ips in
        X-Forwarded-For.  By default it picks the one that the `num_proxies`
        proxy server provides.  Before 0.9 it would always pick the first.

        .. versionadded:: 0.8
        """
        if len(forwarded_for) >= self.num_proxies:
            return forwarded_for[self.num_proxies-1]
        return None

    def get_remote_host(self, forwarded_host):
        """Selects the new remote host from the given list of hosts in
        X-Forwarded-Host.  By default it picks the one that the `num_proxies`
        proxy server provides.

        """
        if len(forwarded_host) >= self.num_proxies:
            return forwarded_host[self.num_proxies-1]
        return None

    def __call__(self, environ, start_response):
        getter = environ.get
        forwarded_proto = getter('HTTP_X_FORWARDED_PROTO', '')
        forwarded_for = getter('HTTP_X_FORWARDED_FOR', '').split(',')
        forwarded_host = getter('HTTP_X_FORWARDED_HOST', '').split(',')
        environ.update({
            'werkzeug.proxy_fix.orig_wsgi_url_scheme':
                getter('wsgi.url_scheme'),
            'werkzeug.proxy_fix.orig_remote_addr':
                getter('REMOTE_ADDR'),
            'werkzeug.proxy_fix.orig_http_host':
                getter('HTTP_HOST')
        })
        forwarded_for = [x for x in [x.strip() for x in forwarded_for] if x]
        forwarded_host = [x for x in [x.strip() for x in forwarded_host] if x]

        remote_addr = self.get_remote_addr(forwarded_for)
        if remote_addr is not None:
            environ['REMOTE_ADDR'] = remote_addr
        if forwarded_host:
            environ['HTTP_HOST'] = self.get_remote_host(forwarded_host)
        if forwarded_proto:
            environ['wsgi.url_scheme'] = forwarded_proto
        return self.app(environ, start_response)


def configure_app(flask_app):
    """Load application configuration to flask.

    Load configuration to Flask object
        :param flask_app: Flask application to configure
        :type flask_app: Flask
    """
    flask_app.config[
        'SWAGGER_UI_DOC_EXPANSION'
    ] = settings.RESTX_SWAGGER_UI_DOC_EXPANSION

    flask_app.config[
        'RESTX_VALIDATE'
    ] = settings.RESTX_VALIDATE

    flask_app.config[
        'RESTX_MASK_SWAGGER'
    ] = settings.RESTX_MASK_SWAGGER

    flask_app.config[
        'ERROR_404_HELP'
    ] = settings.RESTX_ERROR_404_HELP

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
    flask_app.wsgi_app = ProxyFix(flask_app.wsgi_app)

    blueprint = Blueprint(
        'api', __name__,
        url_prefix=settings.API["context_root"]
    )
    api.init_app(blueprint)

    api.add_namespace(equipements_namespace)
    #api.add_namespace(servers_namespace)
    api.add_namespace(recorder_namespace)
    api.add_namespace(monitoring_namespace)

    api_doc = flask_restx.apidoc.apidoc
    api_doc.url_prefix = settings.API["context_root"] + "/doc"
    flask_app.register_blueprint(blueprint)
    requests.urllib3.disable_warnings()


@APP.after_request
def after_request(response):
    """Add CORS Headers."""
    response.headers.add(
        'Access-Control-Allow-Origin',
        '*'
    )
    response.headers.add(
        'Access-Control-Allow-Headers',
        'Content-Type,Authorization'
    )
    response.headers.add(
        'Access-Control-Allow-Methods',
        'GET,PUT,POST,DELETE'
    )
    return response


def main():
    """Application launcher."""
    server_binding = settings.BIND.split(':')
    APP.run(
        debug=settings.FLASK_DEBUG,
        port=int(server_binding[1]),
        host=server_binding[0]
    )


def load_config():
    """Load application config from YAML."""
    LOG.info("Server power consumption daemon is starting")
    with open("conf/webapp-settings.yaml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            settings.BIND = config["BIND"]
            settings.INFLUX = config["INFLUX"]
            settings.MQTT = config["MQTT"] if "MQTT" in config else None
            if settings.MQTT and "port" not in settings.MQTT:
                settings.MQTT["port"] = 1883
            if settings.MQTT and "base_path" not in settings.MQTT:
                settings.MQTT["base_path"] = ""
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
