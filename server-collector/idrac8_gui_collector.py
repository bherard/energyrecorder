# -*- coding: utf-8 -*-
"""Collect power comsumption via DELL IDRAC8 (gui scrapping)."""
# --------------------------------------------------------
# Module Name : terraHouat  power recording IDRAC daemon
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
# File Name   : idrac8_gui_collector.py
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
import xml.etree.ElementTree as ET
from threading import Thread
import requests
from collector import Collector

requests.packages.urllib3.disable_warnings()  # pylint: disable=no-member


class AsyncGet(Thread):
    """Permit asynchronous HTTP GET."""

    # pylint: disable=too-many-arguments
    def __init__(self, url, callback=None,
                 cookies=None, headers=None, auth=None,
                 tags=None):
        """
        Constructor: create an instance of IPMICollector class.

            :param url: URL to get
            :type url: string
            :param callback: callback function to invoke on result
            :type callback: function
            :param cookies: Cookies to send
            :type cookies: dictionary
            :param headers: HTTP headers to send
            :type headers: dictionary
            :param auth: authentication creds
            :type auth: object
            :param tags: any data to forward to callback
            :type tags: object
        """
        Thread.__init__(self)
        self.url = url
        self.cookies = cookies
        self.headers = headers
        self.auth = auth
        self.callback = callback
        self.tags = tags

    def run(self):
        """Execute GET."""
        response = requests.post(self.url,
                                 cookies=self.cookies,
                                 headers=self.headers,
                                 auth=self.auth,
                                 verify=False)
        if self.callback is not None:
            self.callback(response, self.tags)


class IDRAC8GUICollector(Collector):
    """Collect power consumption via DELL IDRAC8 GUI/API."""

    type = "idrac8-gui"

    def get_idrac_power(self, session):
        """Get Power value form IDRAC."""
        power = None
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/data?get=powergraphdata"
        cookies = {
            "-http-session-": session["session_id"]
        }
        headers = {"ST2": session["ST2"]}
        response = requests.post(rqt_url,
                                 cookies=cookies,
                                 headers=headers,
                                 verify=False)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            e_list = (root.find("powergraphdata")
                      .find("lastHourData")
                      .find("powerData")
                      .findall("record"))
            # power = int(e_list[len(e_list)-1].text)
            power = int(e_list[len(e_list)-1].text.split(",")[0])

        else:
            self.log.error(
                "[%s]: Can't get power from IDRAC at %s",
                self.name,
                self.server_conf["base_url"]
            )
            self.log.debug("[%s]: %s", self.name, response.text)
            raise Exception("Can't get power from IDRAC")
        return power

    def login(self):
        """Get session_key from IDRAC."""
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/data/login"
        payload = ("user=" + self.server_conf["user"] +
                   "&password=" + self.server_conf["pass"])
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(rqt_url,
                                 data=payload,
                                 auth=self.pod_auth,
                                 headers=headers,
                                 verify=False)
        if response.status_code == 200:
            session_id = response.cookies["-http-session-"]

            root = ET.fromstring(response.text)
            url = root.find("forwardUrl").text
            url_parts = url.split("ST2=")
            self.log.debug("[%s]: SID=%s", self.name, session_id)
            return {"session_id": session_id, "ST2": url_parts[1]}
        else:
            self.log.error(
                "[%s]: Can't connect IDRAC at %s",
                self.name,
                self.server_conf["base_url"]
            )
            self.log.debug("[%s]: %s", self.name, response.text)
            raise Exception("Can't connect IDRAC")

    def logout(self, session_id):
        """Logout from IDRAC."""
        rqt_url = self.server_conf["base_url"]
        rqt_url += "/data/logout"
        cookies = {
            "-http-session-": session_id
        }
        try:
            # logout may be long, start-it in async mode
            rqt = AsyncGet(rqt_url,
                           tags=self,
                           cookies=cookies)
            rqt.start()
        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectTimeout:
            pass
        except requests.exceptions.ConnectionError:
            pass
        self.log.debug("[%s]: Logged out", self.name)

    def get_power(self):
        """Get power from idrac GUI."""

        power = None
        try:
            session = None
            session = self.login()
            power = self.get_idrac_power(session)
            self.logout(session["session_id"])

        except Exception:  # pylint: disable=broad-except
            if session is not None:
                self.logout(session["session_id"])

            self.log.debug("[%s]: %s", self.name, traceback.format_exc())
            self.log.error(
                "[%s]: Error while trying to connect server (%s): %s",
                self.name,
                self.server_conf["base_url"],
                sys.exc_info()[0]
            )

        return power
