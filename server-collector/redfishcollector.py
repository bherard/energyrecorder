# -*- coding: UTF-8 -*-
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
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Daemon implementation
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
# 1.1.0 - 2018-10-26 : Add feature to synchronize polling of different threads
#

"""Collect power comsumption via redfish API."""

import time
import json
import sys
import traceback
import requests

from collector import Collector


requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class RedfishCollector(Collector):
    """Collect power consumption via HP Redfish rest/redfish API."""

    _chassis_list = None

    def _is_https(self,):
        """Try to determine if host is using https or not."""

        try:
            url = self.server_conf["base_url"]
            self.log.debug("trying to call %s", url)
            requests.get(url, verify=False)
            return True
        except requests.exceptions.ConnectionError:
            url = url.replace("https", "http")
            self.log.debug("trying to call %s", url)
            requests.get(url)
            return False

    def load_chassis_list(self):
        """Get Chassis List for server Redfish API."""
        chassis_list = None

        # Get Chassis list
        while chassis_list is None and self.running:
            try:
                request_url = self.server_conf["base_url"]
                request_url += "/redfish/v1/Chassis/"
                response = requests.get(request_url,
                                        auth=self.pod_auth,
                                        verify=False)
                self.log.debug(
                    "Chassis list at %s ",
                    request_url
                )
                if response.status_code != 200:
                    self.log.error(
                        "Error while calling %s\nHTTP STATUS=%d\nHTTP BODY=%s",
                        request_url,
                        response.status_code,
                        response.text
                    )
                    self.running = False
                else:
                    chassis_list = json.loads(response.text)
            except Exception:  # pylint: disable=locally-disabled,broad-except
                log_msg = "Error while trying to connect server {} ({}): {}"
                log_msg = log_msg.format(self.server_id,
                                         self.server_conf["base_url"],
                                         sys.exc_info()[0])
                self.log.error(log_msg)
                self.log.debug(traceback.format_exc())
                time.sleep(5)
        return chassis_list

    def get_chassis_power(self, chassis_uri):
        """Get PowerMetter values form Redfish API."""
        if chassis_uri[-1:] != '/':
            chassis_uri += '/'
        rqt_url = self.server_conf["base_url"]
        rqt_url += chassis_uri
        rqt_url += "Power/"
        self.log.debug("Power at %s", rqt_url)
        response = requests.get(rqt_url,
                                auth=self.pod_auth,
                                verify=False)
        power_metrics = json.loads(response.text)

        return power_metrics["PowerControl"][0]["PowerConsumedWatts"]

    def pre_run(self):
        """Load chassis list and initialiaze collector."""
        if not self._is_https():
            self.server_conf["base_url"] = (
                self.server_conf["base_url"].replace("https", "http")
            )

        self._chassis_list = self.load_chassis_list()

    def get_power(self):
        """Get Box power."""

        power = 0
        for chassis in self._chassis_list['Members']:

            try:
                power += self.get_chassis_power(chassis["@odata.id"])

            except Exception:  # pylint: disable=broad-except
                # No: default case
                err_text = sys.exc_info()[0]
                log_msg = "Error while trying to connect server {} ({}) \
                            for power query: {}"
                log_msg = log_msg.format(
                    self.server_id,
                    self.server_conf["base_url"],
                    err_text
                )
                self.log.debug(traceback.format_exc())
                self.log.error(err_text)
                return 0

        return power
