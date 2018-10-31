# -*- coding: UTF-8 -*-
# --------------------------------------------------------
# Module Name : terraHouat  power recording Redfish daemon
# Version : 1.0
#
# Software Name : Open NFV functest
# Version :
#
# Copyright © 2018 Orange
# This software is distributed under the Apache 2 license
# <http://www.apache.org/licenses/LICENSE-2.0.html>
#
# -------------------------------------------------------
# File Name   : RedfishCollector.py
#
# Created     : 2018-10
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Daemon implementation
# -------------------------------------------------------
# History     :
# 1.0.0 - 2018-10-30 : Release of the file
#

"""Collect power comsumption base class."""

import logging.config
import time
import sys
import traceback
from threading import Thread
import requests
from common import DataPoster

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class Collector(Thread):
    """Collect power consumption via HP Redfish rest/redfish API."""

    def __init__(self,
                 environment,
                 server_id,
                 server_conf,
                 data_server_conf):
        """
        Constructor: create an instance of IPMICollector class.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param server_id: Server identifier
            :type server_id: string

            :param server_conf: Dictionnatry containing Redfish API
                                    connectivity settings
            :type server_base_url: dictionary
            {
                "base_url": "Redfish API base URL. Ex.: https://localhost:443",
                "user": Basic authentication user,
                "pass": Basic authentication password,
                "poller_name": Polling group name
                "sync_condition": synchronization semaphore
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
        self.server_conf = server_conf
        self.environment = environment
        if server_conf["user"] != "" and\
           server_conf["pass"] != "":
            self.pod_auth = (
                server_conf["user"], server_conf["pass"])
        else:
            self.pod_auth = None
        self.data_server_conf = data_server_conf
        self.condition = server_conf["sync_condition"]
        self.running = False
        self.log = logging.getLogger(__name__)

    def stop(self):
        """
        Stop running Thread.

        Request to the current thread to stop by the end
        of current loop iteration
        """
        log_msg = "Stop called for server"
        log_msg = log_msg.format(self.server_id)
        self.log.debug(log_msg)
        self.running = False

    def get_power(self):
        """Get Power from box (to be implemented)."""
        raise Exception("get_power must be implmented")

    def pre_run(self):
        """Execute code before thread starts."""
        return True

    def post_run(self):
        """Execute code when stread stops."""
        return True

    def run(self):
        """Thread main code."""

        self.running = True
        self.log.info(
            "Starting thread collector for server %s",
            self.server_id
        )

        self.pre_run()
        # Iterate for ever, or near....
        while self.running:
            self.condition.acquire()
            self.condition.wait()
            self.condition.release()

            try:
                power = self.get_power()
                self.log.debug(
                    "Got power form %s (%s): %s",
                    self.server_id,
                    self.server_conf["base_url"],
                    str(power)
                )
                if power is not None and power != 0:

                    # Get measurement time in nano sec.
                    data_time = int(time.time()) * 1000000000

                    self.log.debug("POWER=%s", str(power))
                    data = {
                        "environment": self.environment,
                        "sender": self.server_id,
                        "power": power,
                        "data_time": data_time
                    }
                    self.log.debug(data)
                    data_poster = DataPoster(
                        data,
                        self.data_server_conf
                    )
                    data_poster.start()
                else:
                    self.log.info(
                        "Didn't got power from %s (%s)",
                        self.server_id,
                        self.server_conf["base_url"]
                    )
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

        self.post_run()
        self.log.debug(
            "Thread for server %s is teminated",
            self.server_id
        )
