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
    type = "redfish"

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
                        if "Power" in chassis_def:
                            chassis["HavePower"] = True
                        else:
                            chassis["HavePower"] = False
                        self.log.debug(
                            "[%s]: chassis %s has power data: %s",
                            self.name,
                            chassis["@odata.id"],
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

    def get_chassis_power(self, chassis_uri):
        """Get PowerMetter values form Redfish API."""
        if chassis_uri[-1:] != '/':
            chassis_uri += '/'
        rqt_url = self.server_conf["base_url"]
        rqt_url += chassis_uri
        rqt_url += "Power/"
        self.log.debug(
            "[%s]: Power at %s",
            self.name,
            rqt_url
        )
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
                if chassis["HavePower"]:
                    power += self.get_chassis_power(chassis["@odata.id"])

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

        return power
