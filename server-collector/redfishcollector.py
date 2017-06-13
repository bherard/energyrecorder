# -*- coding: UTF-8 -*-
# --------------------------------------------------------
# Module Name : terraHouat  power recording Redfish daemon
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
#

"""Collect power comsumption via redfish API."""

import logging.config
import time
import json
import sys
import traceback
from threading import Thread
import requests

from common import DataPoster

requests.packages.urllib3.disable_warnings()


class RedfishCollector(Thread):
    """Collect power consumption via HP Redfish rest/redfish API."""

    def __init__(self,
                 environment,
                 server_id,
                 redfish_server_conf,
                 data_server_conf):
        """
        Constructor: create an instance of IPMICollector class.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param server_id: Server identifier
            :type server_id: string

            :param redfish_server_conf: Dictionnatry containing Redfish API
                                    connectivity settings
            :type server_base_url: dictionary
            {
                "base_url": "Redfish API base URL. Ex.: https://localhost:443",
                "user": Basic authentication user,
                "pass": Basic authentication password
                "polling_interval": polling interval diration
            }

            :param data_server_conf: recorder API connection params
            :type data_server_conf dictionarydictionary
            {
                "base_url": "Recorder API base URL",
                "user": Basic authentication user,
                "pass": Basic authentication password
            }
        """
        Thread.__init__(self)
        self.server_id = server_id
        self.redfish_server_conf = redfish_server_conf
        self.environment = environment
        if redfish_server_conf["user"] != "" and\
           redfish_server_conf["pass"] != "":
            self.pod_auth = (
                redfish_server_conf["user"], redfish_server_conf["pass"])
        else:
            self.pod_auth = None
        self.data_server_conf = data_server_conf
        self.running = False
        self.log = logging.getLogger(__name__)

    def stop(self):
        """
        Stop running Thread.

        Request to the current thread to stop by the end
        of current loop iteration
        """
        log_msg = "Stop called for server {}".format(self.server_id)
        self.log.debug(log_msg)
        self.running = False

    def load_chassis_list(self):
        """Get Chassis List for server Redfish API."""
        chassis_list = None

        # Get Chassis list
        while chassis_list is None and self.running:
            try:
                request_url = self.redfish_server_conf["base_url"]
                request_url += "/redfish/v1/Chassis"
                response = requests.get(request_url,
                                        auth=self.pod_auth,
                                        verify=False)
                self.log.debug("Chassis list at " + request_url)
                chassis_list = json.loads(response.text)
            except Exception:  # pylint: disable=locally-disabled,broad-except
                log_msg = "Error while trying to connect server {} ({}): {}"
                log_msg = log_msg.format(self.server_id,
                                         self.redfish_server_conf["base_url"],
                                         sys.exc_info()[0])
                self.log.error(log_msg)
                self.log.debug(traceback.format_exc())
                time.sleep(5)
        return chassis_list

    def get_power(self, chassis_uri):
        """Get PowerMetter values form Redfish API."""
        if chassis_uri[-1:] != '/':
            chassis_uri += '/'
        rqt_url = self.redfish_server_conf["base_url"]
        rqt_url += chassis_uri
        rqt_url += "Power/"
        response = requests.get(rqt_url,
                                auth=self.pod_auth,
                                verify=False)
        self.log.debug("Power at " + rqt_url)
        power_metrics = json.loads(response.text)

        return power_metrics["PowerControl"][0]["PowerConsumedWatts"]

    def run(self):
        """Thread main code."""
        self.running = True

        chassis_list = self.load_chassis_list()
        # Iterate for ever, or near....
        while self.running:
            for chassis in chassis_list['Members']:

                try:
                    power = self.get_power(chassis["@odata.id"])

                    # Get measurement time in nano sec.
                    data_time = int(time.time()) * 1000000000

                    self.log.debug("POWER=" + str(power))
                    data = {
                        "environment": self.environment,
                        "sender": self.server_id,
                        "power": power,
                        "data_time": data_time
                    }
                    self.log.debug(data)
                    data_poster = DataPoster(data,
                                             self.data_server_conf)
                    data_poster.start()
                except Exception:  # pylint: disable=broad-except
                    # No: default case
                    err_text = sys.exc_info()[0]
                    log_msg = "Error while trying to connect server {} ({}) \
                              for power query: {}"
                    log_msg = log_msg.format(
                        self.server_id,
                        self.redfish_server_conf["base_url"],
                        err_text
                    )
                    self.log.debug(traceback.format_exc())
                    self.log.error(err_text)

            time.sleep(self.redfish_server_conf["polling_interval"])
        log_msg = "Thread for server {} is teminated".format(self.server_id)
        self.log.debug(log_msg)
