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
import sys
import traceback
import json
import requests

from collector import Collector

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class INTELGUICollector(Collector):
    """Collect power consumption via DELL INTEL GUI/API."""

    def get_intel_power(self, session):
        """Get Power value form INTEL."""
        power = None
        rqt_url = self.server_conf["base_url"]
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
            log_msg += self.server_conf["base_url"]
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
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/rpc/WEBSES/create.asp"
        payload = ("WEBVAR_USERNAME=" + self.server_conf["user"] +
                   "&WEBVAR_PASSWORD=" + self.server_conf["pass"])
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

            self.log.debug("SID=%s", str(session_id))
            return session_id
        else:
            log_msg = "Can't connect INTEL at "
            log_msg += self.server_conf["base_url"]
            self.log.error(log_msg)
            self.log.debug(response.text)
            raise Exception(log_msg)

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
                self.log.error("Logout error")
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectTimeout:
            pass
        except requests.exceptions.ConnectionError:
            pass
        self.log.debug("Logged out")

    def get_power(self):
        """Get power from intel GUI."""

        power = None
        try:
            session_id = None
            session_id = self.login()
            power = self.get_intel_power(session_id)
            self.logout(session_id)

            self.log.debug("POWER=%s", str(power))
        except Exception:  # pylint: disable=broad-except
            if session_id is not None:
                self.logout(session_id)
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
