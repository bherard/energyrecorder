# -*- coding: utf-8 -*-
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
import json
import sys
import traceback
import requests
from collector import Collector

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class ILOGUICollector(Collector):
    """Collect power consumption via HP ILO rest/redfish API."""

    type = "ilo-gui"

    def get_power_metter(self, session_id):
        """Get PowerMetter values form ILO API."""
        rqt_url = self.server_conf["base_url"]
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
            self.log.error(
                "[%s]: Can't get power from ILO at %s",
                self.name,
                self.server_conf["base_url"]
            )
            self.log.debug("[%s]: %s", self.name, response.text)
            raise Exception("Can't get power from ILO")

    def login(self):
        """Get session_key from ILO."""
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/json/login_session"
        payload = {
            "method": "login",
            "user_login": self.server_conf["user"],
            "password": self.server_conf["pass"]
        }
        response = requests.post(rqt_url,
                                 data=json.dumps(payload),
                                 auth=self.pod_auth,
                                 verify=False)
        if response.status_code == 200:
            json_object = json.loads(response.text)
            return json_object["session_key"]
        else:
            self.log.error(
                "[%s]: Can't connect ILO at %s",
                self.name,
                self.server_conf["base_url"]
            )
            self.log.debug("[%s]: %s", self.name, response.text)
            raise Exception("Can't connect ILO")

    def logout(self, session_key):
        """Logout from ILO."""
        rqt_url = self.server_conf["base_url"]
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
            self.log.debug("[%s]: %s", self.name, response.text)

    def get_power(self):
        """Get power from ILO GUI."""

        power = None
        try:
            session_id = self.login()
            power_metter = self.get_power_metter(session_id)
            self.logout(session_id)

            power = power_metter['samples'][0]['avg']
        except Exception:  # pylint: disable=broad-except
            # Was it and error from ILO?
            self.log.debug("[%s]: %s", self.name, traceback.format_exc())
            self.log.error(
                "[%s]: Error while trying to connect server (%s): %s",
                self.name,
                self.server_conf["base_url"],
                sys.exc_info()[0]
            )
        return power
