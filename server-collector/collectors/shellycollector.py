# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Module Name : terraHouat  power recording Redfish daemon
# Version : 1.1
#
# Software Name : Open NFV functest
# Version :
#
# Copyright © 2017 Orange
# This software is distributed under the Apache 2 license
# <http://www.apache.org/licenses/LICENSE-2.0.html>
#
# -------------------------------------------------------
# File Name   : ShellyCollector.py
#
# Created     : 2022-04
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>,
#
# Description :
#     ShellyPlug collector
# -------------------------------------------------------
# History     :
# 1.0.0 - 2022-04-25 : Release of the file
#

"""Collect power comsumption via ShellyPlug API."""

import time
import json
import logging
import sys
import traceback
import requests

from utils.collector import SensorsCollector


requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class ShellyCollector(SensorsCollector):
    """Collect power consumption via shelly API."""

    _chassis_list = None
    type = "shelly"

    def __init__(self, environment, server_id, server_conf, data_server_conf):
        super().__init__(
            environment, server_id, server_conf, data_server_conf
        )
        if "temperature" not in self.server_conf:
            self.server_conf["temperature"] = True
        if "power" not in self.server_conf:
            self.server_conf["power"] = True


    def get_sensors(self):
        """Get Box power."""

        result = []
        rqt_url = F"http://{self.server_conf['base_url']}/status"
        resp = requests.get(
            rqt_url,
            auth=self.pod_auth,
            verify=False
        )
        if resp.status_code == 200:
            if self.server_conf["temperature"]:
                result.append(
                    self.generate_sensor_data(
                        "temperature",
                        "°C",
                        resp.json()["temperature"]
                    )
                )
            if self.server_conf["power"]:
                result.append(
                    self.generate_sensor_data(
                        "power",
                        "W",
                        resp.json()["meters"][0]["power"]
                    )
                )
        return result


def main():
    """Execute basic test."""
    logging.basicConfig(level=logging.DEBUG)

    redfish_server_conf = {
        "base_url": "1.2.3.4",
        "user": "admin",
        "pass": "foobar",
        "power": True,
        "temperature": True
    }

    the_collector = ShellyCollector(
        "ENV",
        "SRV",
        redfish_server_conf,
        "https://recordingapi.myserver.com"
    )

    logging.debug(the_collector.get_sensors())


if __name__ == "__main__":
    main()
