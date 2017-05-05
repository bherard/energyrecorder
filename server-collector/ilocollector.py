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
import logging.config
import time
import json
import sys
import traceback
from threading import Thread
import calendar
import requests
import dateutil.parser as dp

from common import DataPoster
# from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings()


class ILOCollector(Thread):
    """Collect power consumption via HP ILO rest/redfish API."""

    def __init__(self,
                 environment,
                 server_id,
                 ilo_server_conf,
                 data_server_conf):
        """
        Constructor: create an instance of IPMICollector class.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param server_id: Server identifier
            :type server_id: string

            :param ilo_server_conf: Dictionnatry containing ILO API
                                    connectivity settings
            :type server_base_url: dictionary
            {
                "base_url": "ILO API base URL. Ex.: https://localhost:443",
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
        self.ilo_server_conf = ilo_server_conf
        self.environment = environment
        if ilo_server_conf["user"] != "" and\
           ilo_server_conf["pass"] != "":
            self.pod_auth = (ilo_server_conf["user"], ilo_server_conf["pass"])
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
        """Get Chassis List for server ILO API."""
        chassis_list = None

        # Get Chassis list
        while chassis_list is None and self.running:
            try:
                request_url = self.ilo_server_conf["base_url"]
                request_url += "/rest/v1/Chassis"
                response = requests.get(request_url,
                                        auth=self.pod_auth,
                                        verify=False)
                chassis_list = json.loads(response.text)
            except Exception:  # pylint: disable=locally-disabled,broad-except
                log_msg = "Error while trying to connect server {} ({}): {}"
                log_msg = log_msg.format(self.server_id,
                                         self.ilo_server_conf["base_url"],
                                         sys.exc_info()[0])
                self.log.error(log_msg)
                self.log.debug(traceback.format_exc())
                time.sleep(5)
        return chassis_list

    def get_power_metter(self, resource, chassis):
        """Get PowerMetter values form ILO API."""
        rqt_url = self.ilo_server_conf["base_url"]
        rqt_url += chassis['href']
        rqt_url += resource
        response = requests.get(rqt_url,
                                auth=self.pod_auth,
                                verify=False)
        power_metter = json.loads(response.text)

        return power_metter

    def run(self):
        """Thread main code."""
        self.running = True

        chassis_list = self.load_chassis_list()
        # Iterate for ever, or near....
        while self.running:
            for chassis in chassis_list['links']['Member']:

                try:
                    power_metter = self.get_power_metter(
                        "/PowerMetrics/FastPowerMeter", chassis)

                    # Do we have "/rest" API or redfish ?
                    data_time = None
                    if "PowerDetail" not in power_metter:
                        self.log.debug("ILO2.4")
                        # ILO 2.4 aka ServiceVersion 1.0.0: redfish API
                        power_metter = self.get_power_metter(
                            "/Power/FastPowerMeter", chassis)
                        power = power_metter['PowerDetail'][len(
                            power_metter['PowerDetail']) - 1]['Average']

                        metric_date = dp.parse(power_metter[
                            'PowerDetail'
                        ][
                            len(power_metter['PowerDetail']) - 1
                        ][
                            'Time'])

                        data_time = calendar.timegm(metric_date.timetuple())
                        # Get measurement time in nano sec.
                        data_time *= 1000000000
                    else:
                        # ILO 2.1 aka ServiceVersion 0.9.5: redfish API
                        self.log.debug("ILO2.1")
                        power = power_metter['PowerDetail'][0]['Average']
                        cur_time = time.time()
                        if power_metter['PowerDetail'][0]['Time'] != 'N/A':
                            epoc = float(
                                dp.parse(
                                    '1970-01-01T00:00:00Z').strftime("%s"))
                            measurement_time = power_metter[
                                'PowerDetail'
                            ][
                                0
                            ][
                                'Time'
                            ]
                            measurement_time = dp.parse(measurement_time)
                            measurement_time = measurement_time.strftime("%s")
                            time_offset = epoc - float(measurement_time)
                        else:
                            time_offset = 0
                        # Get measurement time in nano sec.
                        data_time = int(cur_time + time_offset) * 1000000000

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
                    # Was it and error from ILO?
                    if "Messages" in power_metter:
                        # Yeap
                        err_text = power_metter["Messages"][0]["MessageID"]
                    else:
                        # No: default case
                        err_text = sys.exc_info()[0]
                        log_msg = "Error while trying to connect server {} ({}) \
                                  for power query: {}"
                        log_msg = log_msg.format(
                            self.server_id,
                            self.ilo_server_conf["base_url"],
                            err_text
                        )
                        self.log.debug(traceback.format_exc())
                    self.log.error(err_text)

            time.sleep(9.5)
        log_msg = "Thread for server {} is teminated".format(self.server_id)
        self.log.debug(log_msg)
