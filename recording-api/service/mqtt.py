# -*- coding: utf-8 -*-
"""MQTT management."""
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

import datetime
import json
import logging

import paho.mqtt.client as mqtt

import settings

class MQTTService:

    _logger = logging.getLogger(__name__)

    _mqtt_client = None

    def publish(
        self,
        environment,
        equipement,
        scenario,
        step,
        sensor,
        unit,
        value,
        time,
        topology=None
    ):
        """Publish a data to MQTT

        :param environment: related environmenet
        :type environment: str
        :param equipement: related equipement
        :type equipement: str
        :param scenario: current running scenario
        :type scenario: str
        :param step: Current scenaio step
        :type step: str
        :param sensor: related sensor
        :type sensor: str
        :param unit: sensor unit
        :type unit: str
        :param value: data value
        :type value: any
        :param time: Measurement timestamp
        :type time: int
        :param topology: DOC Topology
        :type unit: disct
        """

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
            
            data = {
                "environment": environment,
                "equipement": equipement,
                "scenario": scenario,
                "step": step,
                "sensor": sensor,
                "unit": unit,
                "value": value,
                "timestamp": time if time else int(datetime.datetime.now().timestamp())
            }
            if topology:
                data["topology"] = topology
            self._mqtt_client.publish(
                F'{settings.MQTT["base_path"]}/{environment}/{equipement}/{sensor}',
                json.dumps(
                    data
                )
            )
