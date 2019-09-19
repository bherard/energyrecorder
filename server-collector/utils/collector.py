# -*- coding: utf-8 -*-
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
import sys
import threading
from threading import Thread
import time
import traceback

import requests

from utils.common import SensorsPoster

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class Collector(Thread):
    """Collect power consumption via HP Redfish rest/redfish API."""

    type = "to-be-overloaded-at-implem"

    # Should be replaced by daemon condition at implem class creation
    condition = threading.Condition()

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
        if "user" in server_conf and\
           server_conf["user"] != "" and\
           server_conf["pass"] != "":
            self.pod_auth = (
                server_conf["user"], server_conf["pass"])
        else:
            self.pod_auth = None
        self.data_server_conf = data_server_conf
        self.running = False
        self.ready = False
        self.log = logging.getLogger(__name__)
        self.data_poster = None

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
        return 0  # pylint: disable=unreachable

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
            # Ensure previously posted data are send
            if self.data_poster is not None:
                self.data_poster.join()

            # Running status may have changed while waitting
            if self.running:
                try:
                    # Get measurement time in nano sec.
                    data_time = int(time.time()) * 1000000000
                    self.log.debug(
                        "[%s]: collect time is %d",
                        self.name,
                        data_time
                    )
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
                            "measurements": [
                                {
                                    "sensor": "power",
                                    "unit": "W",
                                    "value": power
                                }
                            ],
                            "data_time": data_time
                        }
                        self.log.debug(
                            "[%s]: %s",
                            self.name,
                            data
                        )

                        self.data_poster = SensorsPoster(
                            data,
                            self.data_server_conf
                        )
                        self.data_poster.name = self.name + "/DataPoster"
                        self.data_poster.start()

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


class SensorsCollector(Thread):
    """Collect Sensors value collect/publish root class."""

    type = "to-be-overloaded-at-implem"

    # Should be replaced by daemon condition at implem class creation
    condition = threading.Condition()

    def __init__(self,
                 environment,
                 server_id,
                 server_conf,
                 data_server_conf):
        """
        Constructor: create an instance of SensorsCollector class.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param server_id: Server identifier
            :type server_id: string

            :param server_conf: Dictionnatry containing child implem params
                Ex: Connectivity setting to server, sensors to collect....
            :type server_conf: dictionary

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
        if "user" in server_conf and\
           server_conf["user"] != "" and\
           server_conf["pass"] != "":
            self.pod_auth = (
                server_conf["user"], server_conf["pass"])
        else:
            self.pod_auth = None
        self.data_server_conf = data_server_conf
        self.running = False
        self.ready = False
        self.log = logging.getLogger(__name__)

        self.data_poster = None
        self._on_send_ok = {}

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

    def get_sensors(self):
        """Get sensors values from equipement (to be implemented)."""
        raise Exception("get_sensors must be implmented")
        return []  # pylint: disable=unreachable

    def pre_run(self):
        """Execute code before thread starts."""
        return True

    def post_run(self):
        """Execute code when stread stops."""
        return True

    def on_send_ok(self, func, *args):
        """
            Register function (with args) to trigger on successfull data send.
        """

        self._on_send_ok["func"] = func
        self._on_send_ok["args"] = args

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
            # Ensure previously posted data are send
            if self.data_poster is not None:
                self.data_poster.join()

            # Running status may have changed while waitting
            if self.running:
                try:
                    # Get measurement time in nano sec.
                    data_time = int(time.time()) * 1000000000
                    self.log.debug(
                        "[%s]: collect time is %d",
                        self.name,
                        data_time
                    )
                    measurements = self.get_sensors()
                    self.log.debug(
                        "[%s]: MESAUREMENT=%s",
                        self.name,
                        measurements
                    )
                    if measurements:

                        for meas in measurements:
                            if "time" not in meas or meas["time"] == 0:
                                meas["time"] = int(time.time()) * 1000000000

                        data = {
                            "environment": self.environment,
                            "sender": self.server_id,
                            "measurements": measurements,
                            "data_time": data_time
                        }
                        self.log.debug(
                            "[%s]: %s",
                            self.name,
                            data
                        )

                        self.data_poster = SensorsPoster(
                            data,
                            self.data_server_conf
                        )
                        if "func" in self._on_send_ok:
                            self.data_poster.on_send_ok(
                                self._on_send_ok["func"],
                                *self._on_send_ok["args"]
                            )

                        self.data_poster.name = self.name + "/DataPoster"
                        self.data_poster.start()
                    else:
                        if "func" in self._on_send_ok:
                            self._on_send_ok["func"](
                                *self._on_send_ok["args"]
                            )
                        self.log.info(
                            "[%s]: Didn't got any measurement from equipement",
                            self.name,
                        )
                except Exception:  # pylint: disable=broad-except
                    # No: default case
                    self.log.error(
                        "[%s]: Error while trying to connect equipement "
                        "for sensors query: %s",
                        self.name,
                        sys.exc_info()[0]
                    )
                    self.log.debug(traceback.format_exc())

        self.post_run()
        self.log.debug(
            "[%s]: Thread for equipement is teminated",
            self.name
        )
