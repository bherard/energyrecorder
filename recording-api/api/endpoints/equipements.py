# -*- coding: utf-8 -*-
"""Equipements monitoring API."""
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
# 1.0.0 - 2019-04-10 : Release of the file
#
import datetime
import json
import logging
import random

import requests
import paho.mqtt.client as mqtt

from flask import request
from flask_restx import Resource
from werkzeug.exceptions import NotFound

import settings
from api.datamodel import API_STATUS, MEASUREMENT_POST
from api.restx import API as api
from api.endpoints.recorder import Recorder
from service.datamodel import APIStatusClass, RunningScenarioClass

NS = api.namespace(
    'equipments',
    description='Equipements monitoring operations'
)


@NS.route('/<string:equipement>/measurements')
class EquipementMeasurements(Resource):
    """Server consumption management API."""

    log = logging.getLogger(__name__)

    _mqtt_client = None

    def _mqtt_publish(
        self,
        environment,
        equipement,
        scenario,
        step,
        sensor,
        unit,
        value,
        time
    ):

        if settings.MQTT:
            if not self._mqtt_client:
                self._mqtt_client = mqtt.Client(str(datetime.datetime.now().timestamp()))
                if "user" in settings.MQTT and settings.MQTT["user"]:
                    self._mqtt_client.username_pw_set(
                        settings.MQTT["user"],
                        settings.MQTT["pass"]
                    )
                self._mqtt_client.connect(
                    settings.MQTT["host"],
                    settings.MQTT["port"],
                )
            
            self._mqtt_client.publish(
                F'{settings.MQTT["base_path"]}/{environment}/{equipement}/{sensor}',
                json.dumps(
                    {
                        "environment": environment,
                        "equipement": equipement,
                        "scenario": scenario,
                        "step": step,
                        "sensor": sensor,
                        "unit": unit,
                        "value": value,
                        "timestamp": time if time else int(datetime.datetime.now().timestamp())
                    }
                )
            )

    @api.expect(MEASUREMENT_POST)
    @api.marshal_with(API_STATUS)
    def post(self, equipement):  # pylint: disable=locally-disabled,no-self-use
        """
        Measurements receiver.

        Store new measurements for a particular equipement
            :param equipement: Equipement identifier
            :type equipement: string
        """

        data = request.json
        recorder_manager = Recorder()

        self.log.info(
            "POST measurements for equiment %s in environment %s",
            equipement,
            data.get("environment")
        )

        time = data.get("time", None)
        try:
            recorder = recorder_manager.load_session(
                data.get("environment"),
                time
            )
        except NotFound as exc:
            if settings.ALWAYS_RECORD:
                recorder = RunningScenarioClass(
                    data.get("environment"),
                    "n/s",
                    "n/s"
                )
            else:
                raise exc

        result = APIStatusClass("OK")

        sm_influx_data = ""
        pm_influx_data = ""
        for measurement in data["measurements"]:
            time = measurement.get("time", None)

            if sm_influx_data != "":
                sm_influx_data += "\n"

            sm_influx_data += "SensorMeasurement,equipement="
            sm_influx_data += equipement.replace(' ', '\\ ')
            sm_influx_data += ",environment="
            sm_influx_data += recorder.environment.replace(' ', '\\ ')
            sm_influx_data += ",scenario="
            sm_influx_data += recorder.scenario.replace(' ', '\\ ')
            sm_influx_data += ",step="
            sm_influx_data += recorder.step.replace(' ', '\\ ')
            sm_influx_data += ",sensor="
            sm_influx_data += measurement["sensor"].replace(' ', '\\ ')
            sm_influx_data += ",unit="
            sm_influx_data += measurement["unit"].replace(' ', '\\ ')
            sm_influx_data += " value="
            sm_influx_data += str(measurement["value"])

            if time and time > 10e+9:
                #Introduce aleat of 0..9999 nano sec to avoid data mixup
                sm_time = time + random.randint(0,9999)
                
                sm_influx_data = sm_influx_data + " " + str(sm_time)

            self._mqtt_publish(
                recorder.environment,
                equipement,
                recorder.scenario,
                recorder.step,
                measurement["sensor"],
                measurement["unit"],
                measurement["value"],
                time
            )

            if measurement["sensor"] == "power":
                if pm_influx_data != "":
                    pm_influx_data += "\n"

                pm_influx_data = "PowerMeasurement,hardware="
                pm_influx_data += equipement.replace(' ', '\\ ')
                pm_influx_data += ",environment="
                pm_influx_data += recorder.environment.replace(' ', '\\ ')
                pm_influx_data += ",scenario="
                pm_influx_data += recorder.scenario.replace(' ', '\\ ')
                pm_influx_data += ",step="
                pm_influx_data += recorder.step.replace(' ', '\\ ')
                pm_influx_data += " power="
                pm_influx_data += str(measurement["value"])

        if settings.INFLUX["user"] is not None:
            auth = (settings.INFLUX["user"], settings.INFLUX["pass"])
        else:
            auth = None

        influx_url = settings.INFLUX["host"]+"/write?db="
        influx_url += settings.INFLUX["db"]
        response = requests.post(
            influx_url,
            data=sm_influx_data.encode("utf-8"),
            auth=auth,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; " +
                                "charset=UTF-8"
            },
            verify=False)
        if response.status_code != 204:
            log_msg = "Error while storing measurment: {}"
            log_msg = log_msg.format(response.text)
            api.abort(500, log_msg)

            response = requests.post(
                influx_url,
                data=pm_influx_data.encode("utf-8"),
                auth=auth,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; " +
                                    "charset=UTF-8"
                },
                verify=False)
            if response.status_code != 204:
                log_msg = "Error while storing measurment: {}"
                log_msg = log_msg.format(response.text)
                api.abort(500, log_msg)

        self.log.info(
            "POST measurements done!"
        )

        return result
