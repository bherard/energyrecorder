# -*- coding: UTF-8 -*-
"""Collect power comsumption via HP ILO (gui scrapping)."""
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
# File Name   : ilo_gui_collector.py
#
# Created     : 2017-06
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
import requests
from common import DataPoster

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class ILOGUICollector(Thread):
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

    def get_power_metter(self, session_id):
        """Get PowerMetter values form ILO API."""
        rqt_url = self.ilo_server_conf["base_url"]
        rqt_url += "/json/power_history_fast"
        cookies = {
            "sessionKey:": session_id
        }
        response = requests.get(rqt_url,
                                auth=self.pod_auth,
                                cookies=cookies,
                                verify=False)
        if response.status_code == 200:
            power_metter = json.loads(response.text)
            return power_metter
        else:
            log_msg = "Can't get power from ILO at "
            log_msg += self.ilo_server_conf["base_url"]
            self.log.error(log_msg)
            self.log.debug(response.text)
            raise Exception(log_msg)

    def login(self):
        """Get session_key from ILO."""
        rqt_url = self.ilo_server_conf["base_url"]
        rqt_url += "/json/login_session"
        payload = {
            "method": "login",
            "user_login": self.ilo_server_conf["user"],
            "password": self.ilo_server_conf["pass"]
        }
        response = requests.post(rqt_url,
                                 data=json.dumps(payload),
                                 auth=self.pod_auth,
                                 verify=False)
        if response.status_code == 200:
            json_object = json.loads(response.text)
            return json_object["session_key"]
        else:
            log_msg = "Can't connect ILO at "
            log_msg += self.ilo_server_conf["base_url"]
            self.log.error(log_msg)
            self.log.debug(response.text)
            raise Exception(log_msg)

    def logout(self, session_key):
        """Logout from ILO."""
        rqt_url = self.ilo_server_conf["base_url"]
        rqt_url += "/json/login_session"
        cookies = {
            "sessionKey:": session_key
        }
        payload = {
            "method": "logout",
            "session_key": session_key
        }
        response = requests.post(rqt_url,
                                 data=json.dumps(payload),
                                 auth=self.pod_auth,
                                 cookies=cookies,
                                 verify=False)
        if response.status_code != 200:
            self.log.debug(response.text)

    def run(self):
        """Thread main code."""
        self.running = True

        # Iterate for ever, or near....
        while self.running:

            try:
                session_id = self.login()
                power_metter = self.get_power_metter(session_id)
                self.logout(session_id)

                # Do we have "/rest" API or redfish ?
                data_time = None
                power = power_metter['samples'][0]['avg']
                cur_time = time.time()
                if power_metter['samples'][0]['time'] != 'N/A':
                    time_offset = int(power_metter[
                        'samples'
                    ][
                        0
                    ][
                        'time'
                    ]) * -1
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
                self.log.debug("Logged out")
            except Exception:  # pylint: disable=broad-except
                # Was it and error from ILO?
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

            time.sleep(self.ilo_server_conf["polling_interval"])

        log_msg = "Thread for server {} is teminated".format(self.server_id)
        self.log.debug(log_msg)
