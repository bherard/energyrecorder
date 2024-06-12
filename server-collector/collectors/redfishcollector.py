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
# File Name   : RedfishCollector.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>,
#               Bertrand Le Lamer <bertrand.lelamer(at)orange.com>
#
# Description :
#     Daemon implementation
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
# 1.1.0 - 2018-10-26 : Add feature to synchronize polling of different threads
# 2.0.0 - 2019-09-26 : Add temperature sensorsreading
#

"""Collect power comsumption via redfish API."""

import time
import json
import logging
import sys
import traceback
import requests

from utils.collector import SensorsCollector


requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class RedfishCollector(SensorsCollector):
    """Collect power consumption via HP Redfish rest/redfish API."""

    _chassis_list = None
    type = "redfish"

    def __init__(self, environment, server_id, server_conf, data_server_conf):
        super().__init__(
            environment, server_id, server_conf, data_server_conf
        )
        if "temperature" not in self.server_conf:
            self.server_conf["temperature"] = True
        if "power" not in self.server_conf:
            self.server_conf["power"] = True

    def _is_https(self,):
        """Try to determine if host is using https or not."""

        try:
            url = self.server_conf["base_url"]
            self.log.debug(
                "[%s]: trying to call %s",
                self.name,
                url
            )
            requests.get(url, verify=False)
            return True
        except requests.exceptions.ConnectionError:
            url = url.replace("https", "http")
            self.log.debug(
                "[%s]: trying to call %s",
                self.name,
                url
            )
            requests.get(url)
            return False

    def get_chassis_def(self, chassis_url):
        """Get chassis def from RedFish."""

        request_url = self.server_conf["base_url"] + chassis_url

        self.log.debug(
            "[%s]: Chassis def at %s ",
            self.name,
            request_url
        )

        response = requests.get(request_url,
                                auth=self.pod_auth,
                                verify=False)
        if response.status_code != 200:
            self.log.error(
                "[%s]: Error while calling %s\nHTTP "
                "STATUS=%d\nHTTP BODY=%s",
                self.name,
                request_url,
                response.status_code,
                response.text
            )
            self.running = False
            return None
        else:
            return json.loads(response.text)

    def load_chassis_list(self):
        """Get Chassis List for server Redfish API."""
        chassis_list = None

        # Get Chassis list
        while chassis_list is None and self.running:
            try:
                request_url = self.server_conf["base_url"]
                request_url += "/redfish/v1/Chassis/"
                self.log.debug(
                    "[%s]: Chassis list at %s ",
                    self.name,
                    request_url
                )
                response = requests.get(request_url,
                                        auth=self.pod_auth,
                                        verify=False)
                if response.status_code != 200:
                    self.log.error(
                        "[%s]: Error while calling %s\nHTTP "
                        "STATUS=%d\nHTTP BODY=%s",
                        self.name,
                        request_url,
                        response.status_code,
                        response.text
                    )
                    self.running = False
                else:
                    chassis_list = json.loads(response.text)
                    for chassis in chassis_list["Members"]:
                        chassis_def = self.get_chassis_def(
                            chassis["@odata.id"]
                        )
                        chassis["Id"] = chassis_def["Id"]
                        if "Thermal" in chassis_def:
                            chassis["HaveThermal"] = True
                        else:
                            chassis["HaveThermal"] = False
                        self.log.debug(
                            "[%s]: chassis %s has Thermal data: %s",
                            self.name,
                            chassis["@odata.id"],
                            chassis["HaveThermal"]
                        )
                        # New URI to get power but depend on SW release of BMC on requested server
                        if "EnvironmentMetrics" in chassis_def:
                            chassis["HaveEnvironmentMetrics"] = True
                            # This does not ensure that PowerWatts is embedded but 1st request will update it
                        else:
                            chassis["HaveEnvironmentMetrics"] = False
                        # Deprecated since 2020 datamodel but can be the only way depending on BMC SW release
                        if "Power" in chassis_def:
                            chassis["HavePower"] = True
                        else:
                            chassis["HavePower"] = False
                        self.log.debug(
                            "[%s]: chassis %s has environemental data: Thermal(%s),"
                            " EnvironementalMetrics(%s), Power --deprecated--(%s)",
                            self.name,
                            chassis["@odata.id"],
                            chassis["HaveThermal"],
                            chassis["HaveEnvironmentMetrics"],
                            chassis["HavePower"]
                        )

            except Exception:  # pylint: disable=locally-disabled,broad-except
                self.log.error(
                    "[%s]: Error while trying to connect server (%s): %s)",
                    self.name,
                    self.server_conf["base_url"],
                    sys.exc_info()[0]
                )
                self.log.debug(
                    "[%s]: %s",
                    self.name,
                    traceback.format_exc()
                )
                time.sleep(5)
        return chassis_list

    def get_chassis_power(self, chassis):
        """Get PowerMetter values form Redfish API."""
        chassis_uri = chassis["@odata.id"]
        if chassis_uri[-1:] != '/':
            chassis_uri += '/'
        rqt_url = self.server_conf["base_url"]
        rqt_url += chassis_uri

        chassis_power = 0
        # EnvironmentMetrics is the nominal uri to get power of the server
        if chassis["HaveEnvironmentMetrics"]:
            self.log.debug(
                "[%s]: Power at %s",
                self.name,
                rqt_url + "EnvironmentMetrics/"
            )
            response = requests.get(rqt_url + "EnvironmentMetrics/",
                                    auth=self.pod_auth,
                                    verify=False)
            power_metrics = json.loads(response.text)
            
            if "PowerWatts" in power_metrics:
                chassis_power += power_metrics["PowerWatts"]["Reading"]
                self.log.debug(
                    "[%s]: Power collected: [%s]",
                    self.name,
                    chassis_power
                )
            else:
                chassis["HaveEnvironmentMetrics"] = False
        
        if not chassis["HaveEnvironmentMetrics"] and chassis["HavePower"]:
            # for older BMC SW release we could use deprecated way still in use
            self.log.debug(
                "[%s]: Power at %s",
                self.name,
                rqt_url + "Power/"
            )
            response = requests.get(rqt_url + "Power/",
                                    auth=self.pod_auth,
                                    verify=False)
            power_metrics = json.loads(response.text)

            for pwr in power_metrics["PowerControl"]:
                # PowerControl is a list which nb elements depends on provider 
                # and BMC SW release
                # PhysicalContext = Chassis ensure we are on the right list element
                # in case BMC is not right regarding datamodel we use 1st element
                # which id to ensure it is the first is slighty dependent on provider
                if ("PhysicalContext" in pwr and 
                    pwr["PhysicalContext"] == "Chassis"
                    ) or \
                    pwr["@odata.id"] == chassis_uri+"Power#/PowerControl/0" or \
                    pwr["@odata.id"] == chassis_uri+"Power/#/PowerControl/0":
                        if pwr["PowerConsumedWatts"].isdigit():
                            chassis_power += pwr["PowerConsumedWatts"]
                            self.log.debug(
                                "[%s]: Power collected: [%s]",
                                self.name,
                                chassis_power
                            )
                        else:
                            self.log.error(
                                "[%s]: powerConsumedWatts not digit [%s]",
                                self.name,
                                pwr["PowerConsumedWatts"]
                            )

        return chassis_power

    def get_chassis_thermal(self, chassis_uri, chassis_id):
        """Get ThermalMetter values form Redfish API."""
        result = []
        if chassis_uri[-1:] != '/':
            chassis_uri += '/'
        rqt_url = self.server_conf["base_url"]
        rqt_url += chassis_uri
        rqt_url += "Thermal/"
        self.log.debug(
            "[%s]: Thermal at %s",
            self.name,
            rqt_url
        )
        response = requests.get(
            rqt_url,
            auth=self.pod_auth,
            verify=False
        )
        thermal_metrics = json.loads(response.text)
        
        self.log.debug(
            "[%s]: Thermal collected",
            self.name
        )

        for thermal in thermal_metrics["Temperatures"]:
            if thermal["Status"]["State"] == "Enabled":
                temp = self.generate_sensor_data(
                    chassis_id + "/" + thermal["Name"],
                    "Celsius",
                    thermal["ReadingCelsius"]
                )
                result.append(temp)
        return result

    def pre_run(self):
        """Load chassis list and initialiaze collector."""
        if not self._is_https():
            self.server_conf["base_url"] = (
                self.server_conf["base_url"].replace("https", "http")
            )

        self._chassis_list = self.load_chassis_list()

    def get_sensors(self):
        """Get Box power."""

        if not self._chassis_list:
            # Ensure chassis list is loaded
            running = self.running
            self.running = True
            self.pre_run()
            self.running = running

        power = 0
        thermal = []
        for chassis in self._chassis_list['Members']:

            try:
                if chassis["HaveThermal"] and self.server_conf["temperature"]:
                    thermal += self.get_chassis_thermal(
                        chassis["@odata.id"], chassis["Id"]
                    )
                if chassis["HavePower"] and self.server_conf["power"]:
                        power += self.get_chassis_power(chassis)

            except Exception:  # pylint: disable=broad-except
                # No: default case
                err_text = sys.exc_info()[0]
                log_msg = "Error while trying to connect server {} ({}) \
                            for power query: {}"
                log_msg = log_msg.format(
                    self.name,
                    self.server_conf["base_url"],
                    err_text
                )
                self.log.debug(
                    "[%s]: %s",
                    self.name,
                    traceback.format_exc()
                )
                self.log.error(
                    "[%s]: %s",
                    self.name, err_text
                )
                return 0
        pwr = []
        pwr.append(self.generate_sensor_data("power", "W", power))
        return pwr + thermal


def main():
    """Execute basic test."""
    logging.basicConfig(level=logging.DEBUG)

    redfish_server_conf = {
        "base_url": "https://127.0.0.1:2222",
        "user": "opnfv",
        "pass": "opnfv2018",
        "power": True,
        "temperature": True
    }

    the_collector = RedfishCollector(
        "ENV",
        "SRV",
        redfish_server_conf,
        "https://recordingapi.myserver.com"
    )

    logging.debug(the_collector.get_sensors())


if __name__ == "__main__":
    main()
