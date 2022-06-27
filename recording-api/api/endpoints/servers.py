# -*- coding: utf-8 -*-
"""Servers compuption API."""
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
# File Name   : api/endpoints/servers.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Servers management
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
#
import logging
import requests

from flask import request
from flask_restx import Resource

import settings
from api.datamodel import POWER_MEASUREMENT, POWER_POST
from api.restx import API as api
from service.datamodel import PowerMeasurementClass, RunningScenarioClass
from service.exception import RecordingException
from service.recorder import RecorderService


NS = api.namespace('servers', description='Operations related to servers')


@NS.route('/<string:server>/consumption')
@NS.deprecated
class ServerConsumption(Resource):
    """Server consumption management API."""

    log = logging.getLogger(__name__)

    @api.expect(POWER_POST)
    @api.marshal_with(POWER_MEASUREMENT)
    def post(self, server):  # pylint: disable=locally-disabled,no-self-use
        """
        Power consumption receiver (see /equipments/{equipement}/measurements).

        Use instead /equipments/{equipement}/measurements with
        <code>[{"sensor": "power", "unit": "W", "value": power-value}]</code>
        as measurements payload<hr>

        Store a new power consumption measurement for a particular server
            :param server: Environement identifier
            :type server: string
        """

        data = request.json
        recorder_manager = RecorderService()

        self.log.info(
            "POST server %s consumption %s in environment %s",
            server,
            data.get("power"),
            data.get("environment")
        )

        time = data.get("time", None)
        try:
            recorder = recorder_manager.load_session(
                data.get("environment"),
                time
            )
        except RecordingException as exc:
            if exc.http_status == 404:
                if settings.ALWAYS_RECORD:
                    recorder = RunningScenarioClass(
                        data.get("environment"),
                        "n/s",
                        "n/s"
                    )
            else:
                raise exc

        result = PowerMeasurementClass(
            recorder.environment,
            data.get("power"),
            recorder.scenario,
            recorder.step
        )

        influx_data = "PowerMeasurement,hardware="
        influx_data += server.replace(' ', '\\ ')
        influx_data += ",environment="
        influx_data += result.environment.replace(' ', '\\ ')
        influx_data += ",scenario="
        influx_data += result.scenario.replace(' ', '\\ ')
        influx_data += ",step="
        influx_data += result.step.replace(' ', '\\ ')
        influx_data += " power="
        influx_data += str(data.get("power"))
        if time is not None:
            influx_data = influx_data + " " + str(time)

        if settings.INFLUX["user"] is not None:
            auth = (settings.INFLUX["user"], settings.INFLUX["pass"])
        else:
            auth = None

        influx_url = settings.INFLUX["host"]+"/write?db="
        influx_url += settings.INFLUX["db"]
        response = requests.post(
            influx_url,
            data=influx_data,
            auth=auth,
            verify=False)
        if response.status_code != 204:
            log_msg = "Error while storing measurment: {}"
            log_msg = log_msg.format(response.text)
            api.abort(500, log_msg)

        influx_data = "SensorMeasurement,equipement="
        influx_data += server.replace(' ', '\\ ')
        influx_data += ",environment="
        influx_data += recorder.environment.replace(' ', '\\ ')
        influx_data += ",scenario="
        influx_data += recorder.scenario.replace(' ', '\\ ')
        influx_data += ",step="
        influx_data += recorder.step.replace(' ', '\\ ')
        influx_data += ",sensor=power"
        influx_data += ",unit=W"
        influx_data += " value="
        influx_data += str(data["power"])

        response = requests.post(
            influx_url,
            data=influx_data,
            auth=auth,
            verify=False)
        if response.status_code != 204:
            log_msg = "Error while storing measurment: {}"
            log_msg = log_msg.format(response.text)
            api.abort(500, log_msg)

        return result
