# -*- coding: UTF-8 -*-
"""Collect power comsumption via HP ILO."""
# --------------------------------------------------------
# Module Name : terraHouat  power recording ILO daemon
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
# File Name   : iloCollector.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Daemon implementation
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
#
import time
import json
import sys
import traceback
import requests

from collector import Collector

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class ILOCollector(Collector):
    """Collect power consumption via HP ILO rest/redfish API."""

    _chassis_list = None

    def load_chassis_list(self):
        """Get Chassis List for server ILO API."""
        chassis_list = None

        # Get Chassis list
        while chassis_list is None and self.running:
            try:
                request_url = self.server_conf["base_url"]
                request_url += "/rest/v1/Chassis"
                response = requests.get(request_url,
                                        auth=self.pod_auth,
                                        verify=False)
                chassis_list = json.loads(response.text)
            except Exception:  # pylint: disable=locally-disabled,broad-except
                self.log.error(
                    "[%s]: Error while trying to connect server (%s): %s",
                    self.name,
                    self.server_conf["base_url"],
                    sys.exc_info()[0]
                )
                self.log.debug("[%s]: %s", self.name, traceback.format_exc())
                time.sleep(5)
        return chassis_list

    def get_power_metter(self, resource, chassis):
        """Get PowerMetter values form ILO API."""
        rqt_url = self.server_conf["base_url"]
        rqt_url += chassis['href']
        rqt_url += resource
        response = requests.get(rqt_url,
                                auth=self.pod_auth,
                                verify=False)
        power_metter = json.loads(response.text)

        return power_metter

    def pre_run(self):
        """Load chassis list befor starting."""

        self._chassis_list = self.load_chassis_list()

    def get_power(self):
        """Get power form ILO API."""

        power = 0
        for chassis in self._chassis_list['links']['Member']:

            try:
                power_metter = self.get_power_metter(
                    "/PowerMetrics/FastPowerMeter", chassis)

                if "PowerDetail" not in power_metter:
                    self.log.debug("[%s]: ILO2.4", self.name)
                    # ILO 2.4 aka ServiceVersion 1.0.0: redfish API
                    power_metter = self.get_power_metter(
                        "/Power/FastPowerMeter", chassis)
                    power += power_metter['PowerDetail'][len(
                        power_metter['PowerDetail']) - 1]['Average']

                else:
                    # ILO 2.1 aka ServiceVersion 0.9.5: redfish API
                    self.log.debug("[%s]: ILO2.1", self.name)
                    power += power_metter['PowerDetail'][0]['Average']
            except Exception:  # pylint: disable=broad-except
                # Was it and error from ILO?
                if "Messages" in power_metter:
                    # Yeap
                    err_text = power_metter["Messages"][0]["MessageID"]
                else:
                    # No: default case
                    err_text = sys.exc_info()[0]
                    self.log.debug(
                        "[%s]: %s",
                        self.name,
                        traceback.format_exc()
                    )
                self.log.error("[%s]: %s", self.name, err_text)
                return None
        return power
