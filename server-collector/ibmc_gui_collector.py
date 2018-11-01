# -*- coding: UTF-8 -*-
"""Collect power comsumption via Huawei iBmc Web Console (gui scrapping)."""
# --------------------------------------------------------
# Module Name : terraHouat  power recording Huawei iBmc GUI daemon
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
# File Name   : ibmc_gui_collector.py
#
# Created     : 2018-03
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Daemon implementation
# -------------------------------------------------------
# History     :
# 1.0.0 - 2018-03-26 : Release of the file
#
import sys
import traceback
import urllib
import json
import requests

from collector import Collector

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class IBMCGUICollector(Collector):
    """Collect power consumption via DELL Huawei iBmc GUI/API."""

    _USER_AGENT = "Mozilla Chrome"

    def get_ibmc_power(self, session):
        """Get Power value form Huawei iBmc."""
        power = None
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/bmc/php/getmultiproperty.php"
        cookies = {
            "SessionId3": session["cookie"],
            "PowerUnits": "1"
        }
        headers = {"User-Agent": self._USER_AGENT,
                   "Content-Type": "application/x-www-form-urlencoded"}
        payload = (
            "token=" + urllib.quote_plus(session["token"]) +
            "&str_input=%5B%7B%22class_name%22%3A%22MeIn" +
            "fo%22%2C%22obj_name%22%3A+%22MeInfo%22%2C%2" +
            "2property_list%22%3A%5B%22CpuCurPower%22%2C" +
            "%22MemCurPower%22%5D%7D%2C%7B%22class_name%" +
            "22%3A%22SysPower%22%2C%22obj_name%22%3A+%22" +
            "syspower%22%2C%22property_list%22%3A%5B%22P" +
            "ower%22%2C%22PowerConsumption%22%2C%22PeakV" +
            "alue%22%2C%22PeakTime%22%2C%22RecordBeginTi" +
            "me%22%2C%22AveragePower%22%5D%7D%2C%7B%22cl" +
            "ass_name%22%3A%22PowerCapping%22%2C%22obj_n" +
            "ame%22%3A+%22powercapping%22%2C%22property_" +
            "list%22%3A%5B%22BaseValue%22%2C%22TopValue%" +
            "22%2C%22Enable%22%2C%22LimitValue%22%2C%22F" +
            "ailAction%22%2C%22ManualSetEnable%22%5D%7D%5D")
        self.log.debug("[%s]: Getting power at %s", self.name, rqt_url)
        response = requests.post(rqt_url,
                                 cookies=cookies,
                                 headers=headers,
                                 data=payload,
                                 verify=False)
        if response.status_code == 200:
            json_str = self.clean_json(response.text)
            self.log.debug("[%s]: %s", self.name, json_str)
            json_data = json.loads(json_str)
            power = json_data["SysPower"][0]["Power"]
        else:
            self.log.error(
                "[%s]: Can't get power from Huawei iBmc at %s",
                self.name,
                self.server_conf["base_url"]
            )
            self.log.debug("[%s]: %s", self.name, response.text)
            raise Exception("Can't get power from Huawei iBmc")
        return power

    def clean_json(self, str_json):
        """Clean returned pseudo JSON by Intel Web Console."""
        self.log.debug("[%s]: Cleanning returned JSON", self.name)
        new_json = str_json.replace("%22", '"')
        if new_json[0:1] != "{":
            result = "%s" % (new_json[1:])
        else:
            result = new_json

        return result

    def _get_token(self, session_id):
        """Get token from Huawei iBmc"""
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/bmc/php/gettoken.php"
        cookies = {
            "SessionId3": session_id
        }
        headers = {"User-Agent": self._USER_AGENT}
        self.log.debug("[%s]: Getting token at %s", rqt_url, self.name)
        response = requests.post(rqt_url,
                                 cookies=cookies,
                                 headers=headers,
                                 verify=False)
        if response.status_code == 200:
            self.log.debug("[%s]: Token=%s", self.name, response.text)
            return response.text
        else:
            self.log.error(
                "[%s]: Get token status: %d (%s)",
                self.name,
                response.status_code,
                response.text
            )
            raise Exception("Unable to get token")

    def login(self):
        """Get session_key from Huawei iBmc."""
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/bmc/php/processparameter.php"
        payload = ("check_pwd=" +
                   urllib.quote_plus(self.server_conf["pass"]) +
                   "&logtype=0" +
                   "&user_name=" +
                   urllib.quote_plus(self.server_conf["user"]) +
                   "&func=AddSession" +
                   "&IsKvmApp=0")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.log.debug("[%s]: Login at %s", self.name, rqt_url)
        response = requests.post(rqt_url,
                                 data=payload,
                                 headers=headers,
                                 verify=False)
        if response.status_code == 200:
            for cookie in response.cookies:
                if "SessionId" in cookie.name:
                    session_id = cookie.value
                    self.log.debug(
                        "[%s]: Session ID=%s",
                        self.name,
                        session_id
                    )
                    token = self._get_token(session_id)
                    break
            assert session_id
            assert token
            return {"cookie": session_id, "token": token}
        else:
            self.log.error(
                "[%s]: Can't connect Huawei iBmc at %s",
                self.name,
                self.server_conf["base_url"]
            )
            self.log.debug("[%s]: %s", self.name, response.text)
            raise Exception("Can't connect Huawei iBmc")

    def logout(self, session_id):
        """Logout from Huawei iBmc."""
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/bmc/php/processparameter.php"
        cookies = {
            "SessionId3": session_id["cookie"]
        }
        headers = {"User-Agent": self._USER_AGENT,
                   "Content-Type": "application/x-www-form-urlencoded"}
        payload = ("token=" + session_id["token"] +
                   "&func=DelSession")
        try:
            response = requests.post(rqt_url,
                                     auth=self.pod_auth,
                                     cookies=cookies,
                                     headers=headers,
                                     data=payload,
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
        """Get power form iBMC GUI."""

        power = None
        try:
            session_id = None
            session_id = self.login()
            power = self.get_ibmc_power(session_id)
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
