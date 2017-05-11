# -*- coding: UTF-8 -*-
"""Recorder API Management."""
# --------------------------------------------------------
# Module Name : power recording API
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
# File Name   : api/endpoints/monitoring.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     API monitoring
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-05-11 : Release of the file
#

import logging
import urllib
import requests

from flask_restplus import Resource
import settings
from api.restplus import API as api


NS = api.namespace('monitoring',
                   description='API monitoring')


@NS.route('/ping')
class Ping(Resource):
    """API monitoring Ping class."""

    logger = logging.getLogger(__name__)

    def connect_influx(self):
        """Try to connect influxDB."""
        self.logger.debug("ping called")
        result = "OK"
        if settings.INFLUX["user"] is not None:
            auth = (settings.INFLUX["user"], settings.INFLUX["pass"])
        else:
            auth = None

        influx_url = settings.INFLUX["host"] + "/query?q="
        influx_url += urllib.quote_plus("SHOW DATABASES")
        influx_url += "&db=" + urllib.quote_plus(settings.INFLUX["db"])
        response = requests.get(influx_url, auth=auth, timeout=1)
        if response.status_code != 200:
            raise Exception("Unable to connect influxDB")
        return result

    def get(self):
        """Return API status."""
        return self.connect_influx()
