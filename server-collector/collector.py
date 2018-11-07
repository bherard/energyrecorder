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
        self.name = "{}/{}".format(self.type, server_id)
        self.server_conf = server_conf
        self.environment = environment
        if server_conf["user"] != "" and\
           server_conf["pass"] != "":
            self.pod_auth = (
                server_conf["user"], server_conf["pass"])
        else:
            self.pod_auth = None
        self.data_server_conf = data_server_conf
        self.running = False
        self.ready = False
        self.log = logging.getLogger(__name__)

    def stop(self):
        """
        Stop running Thread.

        Request to the current thread to stop by the end
        of current loop iteration
        """
        self.log.debug(
            "[%s]: Stop called for server",
            self.name
        )
        self.running = False
        self.ready = False

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

        self.log.info(
            "[%s]: Starting collector thread",
            self.name
        )

        self.running = True
        try:
            self.pre_run()
            self.ready = True
        except Exception:  # pylint: disable=locally-disabled,broad-except
            self.log.exception(
                "[%s]: Error while executing pre_run. "
                "\n\n\tSTOPING THREAD !!\n\n",
                self.name
            )
            self.running = False
        # Iterate for ever, or near....
        while self.running:

            # Wait for next request
            self.log.debug(
                "[%s]: Collector ready for next read",
                self.name
            )
            self.condition.acquire()
            self.condition.wait()
            self.condition.release()

            # Running status may have changed while waitting
            if self.running:
                try:
                    self.log.debug(
                        "[%s]: requesting power",
                        self.name
                    )
                    # Get measurement time in nano sec.
                    data_time = int(time.time()) * 1000000000
                    power = self.get_power()
                    self.log.debug(
                        "[%s]: POWER=%s",
                        self.name,
                        str(power)
                    )
                    if power is not None and power != 0:

                        data = {
                            "environment": self.environment,
                            "sender": self.server_id,
                            "power": power,
                            "data_time": data_time
                        }
                        self.log.debug(
                            "[%s]: %s",
                            self.name,
                            data
                        )
                        data_poster = DataPoster(
                            data,
                            self.data_server_conf
                        )
                        data_poster.name = self.name
                        data_poster.start()
                    else:
                        self.log.info(
                            "[%s]: Didn't got power from server",
                            self.name,
                        )
                except Exception:  # pylint: disable=broad-except
                    # No: default case
                    self.log.error(
                        "[%s]: Error while trying to connect server "
                        "for power query: %s",
                        self.name,
                        sys.exc_info()[0]
                    )
                    self.log.debug(traceback.format_exc())

        self.post_run()
        self.log.debug(
            "[%s]: Thread for server is teminated",
            self.name
        )
