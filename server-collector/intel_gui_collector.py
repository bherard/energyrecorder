# -*- coding: UTF-8 -*-
"""Collect power comsumption via INTEL Web Console (gui scrapping)."""
# --------------------------------------------------------
# Module Name : terraHouat  power recording INTEL GUI daemon
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
# File Name   : intel_gui_collector.py
#
# Created     : 2017-06
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Daemon implementation
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-06-28 : Release of the file
#
import logging.config
import time
import sys
import traceback
import json
from threading import Thread
import requests
from common import DataPoster

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class INTELGUICollector(Thread):
    """Collect power consumption via DELL INTEL GUI/API."""

    def __init__(self,
                 environment,
                 server_id,
                 intel_server_conf,
                 data_server_conf):
        """
        Constructor: create an instance of INTELGUICollector class.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param server_id: Server identifier
            :type server_id: string

            :param intel_server_conf: Dictionnatry containing INTEL
                                      connectivity settings
            :type server_base_url: dictionary
            {
                "base_url": "INTEL base URL. Ex.: https://localhost:443",
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
        self.intel_server_conf = intel_server_conf
        self.environment = environment
        if intel_server_conf["user"] != "" and\
           intel_server_conf["pass"] != "":
            self.pod_auth = (intel_server_conf["user"],
                             intel_server_conf["pass"])
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

    def get_power(self, session):
        """Get Power value form INTEL."""
        power = None
        rqt_url = self.intel_server_conf["base_url"]
        rqt_url += "/rpc/getpowerstat.asp"
        cookies = {
            "SessionCookie": session
        }
        self.log.debug("Getting power at %s", rqt_url)
        response = requests.get(rqt_url,
                                cookies=cookies,
                                verify=False)
        if response.status_code == 200:
            json_str = self.clean_json(response.text, "GETNMSTATISTICS")
            json_data = json.loads(json_str)
            power = json_data[
                "WEBVAR_STRUCTNAME_GETNMSTATISTICS"][0]["LSB_CURR"]
        else:
            log_msg = "Can't get power from INTEL at "
            log_msg += self.intel_server_conf["base_url"]
            self.log.error(log_msg)
            self.log.debug(response.text)
            raise Exception(log_msg)
        return power

    def clean_json(self, str_json, var_name):
        """Clean returned pseudo JSON by Intel Web Console."""
        self.log.debug("Cleanning returned JSON")
        new_json = str_json.replace("'", '"')
        new_json = new_json.replace("//Dynamic Data Begin\n", "")
        new_json = new_json.replace(";", "")
        new_json = new_json.replace("//Dynamic data end", "")
        new_json = new_json.replace(" WEBVAR_JSONVAR_" + var_name + " =", "")
        new_json = new_json.replace(
            "WEBVAR_STRUCTNAME_" + var_name,
            '"WEBVAR_STRUCTNAME_' + var_name + '"')
        new_json = new_json.replace("HAPI_STATUS", '"HAPI_STATUS"')

        return new_json

    def login(self):
        """Get session_key from INTEL."""
        rqt_url = self.intel_server_conf["base_url"]
        rqt_url += "/rpc/WEBSES/create.asp"
        payload = ("WEBVAR_USERNAME=" + self.intel_server_conf["user"] +
                   "&WEBVAR_PASSWORD=" + self.intel_server_conf["pass"])
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.log.debug("Login at %s", rqt_url)
        response = requests.post(rqt_url,
                                 data=payload,
                                 auth=self.pod_auth,
                                 headers=headers,
                                 verify=False)
        if response.status_code == 200:
            json_str = self.clean_json(response.text, "WEB_SESSION")
            json_data = json.loads(json_str)

            session_id = json_data[
                "WEBVAR_STRUCTNAME_WEB_SESSION"
            ][0]["SESSION_COOKIE"]

            self.log.debug("SID=" + session_id)
            return session_id
        else:
            log_msg = "Can't connect INTEL at "
            log_msg += self.intel_server_conf["base_url"]
            self.log.error(log_msg)
            self.log.debug(response.text)
            raise Exception(log_msg)

    def logout(self, session_id):
        """Logout from INTEL."""
        rqt_url = self.intel_server_conf["base_url"]
        rqt_url += "/rpc/WEBSES/logout.asp"
        cookies = {
            "SessionCookie": session_id
        }
        try:
            response = requests.get(rqt_url,
                                    auth=self.pod_auth,
                                    cookies=cookies,
                                    verify=False)
            if response.status_code != 200:
                self.log.error("Logout error")
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectTimeout:
            pass
        except requests.exceptions.ConnectionError:
            pass
        self.log.debug("Logged out")

    def run(self):
        """Thread main code."""
        self.running = True

        # Iterate for ever, or near....
        while self.running:

            try:
                session_id = None
                session_id = self.login()
                power = self.get_power(session_id)
                self.logout(session_id)

                self.log.debug("POWER=" + str(power))
                data_time = int(time.time()) * 1000000000
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
                if session_id is not None:
                    self.logout(session_id)
                err_text = sys.exc_info()[0]
                log_msg = "Error while trying to connect server {} ({}) \
                          for power query: {}"
                log_msg = log_msg.format(
                    self.server_id,
                    self.intel_server_conf["base_url"],
                    err_text
                )
                self.log.debug(traceback.format_exc())
                self.log.error(err_text)

            time.sleep(self.intel_server_conf["polling_interval"])

        log_msg = "Thread for server {} is teminated".format(self.server_id)
        self.log.debug(log_msg)
