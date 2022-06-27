# -*- coding: utf-8 -*-
"""Monitoring management."""
# --------------------------------------------------------
# Module Name : power recording API
# Version : 1.0
#
# Copyright © 2022 Orange
# This software is distributed under the Apache 2 license
# <http://www.apache.org/licenses/LICENSE-2.0.html>
#
# -------------------------------------------------------
# Created     : 2022-06
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Scenarios and scenarios steps management.

import json
import logging
import urllib

import requests

from service.datamodel import APIStatusClass
import settings

class MonitoringService:
    """Monitoring services."""

    logger = logging.getLogger(__name__)

    def connect_influx(self):
        """Try to connect influxDB."""

        result = APIStatusClass("OK")
        if settings.INFLUX["user"] is not None:
            auth = (settings.INFLUX["user"], settings.INFLUX["pass"])
        else:
            auth = None

        query = 'SHOW RETENTION POLICIES ON "{}"'
        query = query.format(settings.INFLUX["db"])
        influx_url = settings.INFLUX["host"] + "/query?q="
        influx_url += urllib.parse.quote(query)
        influx_url += "&db=" + urllib.parse.quote(settings.INFLUX["db"])
        response = requests.get(influx_url, auth=auth, timeout=1, verify=False)
        if response.status_code != 200:
            error = json.loads(response.text)
            raise Exception("Unable to connect influxDB: " + error["error"])
        json_object = json.loads(response.text)
        if "error" in json_object["results"][0]:
            raise Exception(json_object["results"][0]["error"])
        return result
