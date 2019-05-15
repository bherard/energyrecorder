# -*- coding: utf-8 -*-
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
import sys
import traceback
import json
import requests

from utils.collector import Collector

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class INTELGUICollector(Collector):
    """Collect power consumption via DELL INTEL GUI/API."""

    type = "intel-gui"

    def get_intel_power(self, session):
        """Get Power value form INTEL."""
        power = None
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/rpc/getpowerstat.asp"
        cookies = {
            "SessionCookie": session
        }
        self.log.debug("[%s]: Getting power at %s", self.name, rqt_url)
        response = requests.get(rqt_url,
                                cookies=cookies,
                                verify=False)
        if response.status_code == 200:
            json_str = self.clean_json(response.text, "GETNMSTATISTICS")
            json_data = json.loads(json_str)
            power = json_data[
                "WEBVAR_STRUCTNAME_GETNMSTATISTICS"][0]["LSB_CURR"]
        else:
            self.log.error(
                "[%s]: Can't get power from INTEL at %s",
                self.name,
                self.server_conf["base_url"]
            )
            self.log.debug("[%s]: %s", self.name, response.text)
            raise Exception("Can't get power from INTEL")
        return power

    def clean_json(self, str_json, var_name):
        """Clean returned pseudo JSON by Intel Web Console."""
        self.log.debug("[%s]: Cleanning returned JSON", self.name)
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
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/rpc/WEBSES/create.asp"
        payload = ("WEBVAR_USERNAME=" + self.server_conf["user"] +
                   "&WEBVAR_PASSWORD=" + self.server_conf["pass"])
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.log.debug("[%s]: Login at %s", self.name, rqt_url)
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

            self.log.debug("[%s]: SID=%s", self.name, str(session_id))
            return session_id
        else:
            self.log.error(
                "[%s]: Can't connect INTEL at %s",
                self.name,
                self.server_conf["base_url"]
            )
            self.log.debug("[%s]: %s", self.name, response.text)
            raise Exception("Can't connect INTEL")

    def logout(self, session_id):
        """Logout from INTEL."""
        rqt_url = self.server_conf["base_url"]
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
                self.log.error("[%s]: Logout error", self.name)
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectTimeout:
            pass
        except requests.exceptions.ConnectionError:
            pass
        self.log.debug("[%s]: Logged out", self.name)

    def get_power(self):
        """Get power from intel GUI."""

        power = None
        try:
            session_id = None
            session_id = self.login()
            power = self.get_intel_power(session_id)
            self.logout(session_id)

        except Exception:  # pylint: disable=broad-except
            if session_id is not None:
                self.logout(session_id)

            self.log.debug("[%s]: %s", self.name, traceback.format_exc())
            self.log.error(
                "[%s]: Error while trying to connect server (%s): %s",
                self.name,
                self.server_conf["base_url"],
                sys.exc_info()[0]
            )

        return power
