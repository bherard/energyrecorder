# -*- coding: UTF-8 -*-
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
import logging.config
import time
import sys
import traceback
import xml.etree.ElementTree as ET
from threading import Thread
import requests
from common import DataPoster

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


class IDRAC8GUICollector(Thread):
    """Collect power consumption via DELL IDRAC8 GUI/API."""

    def __init__(self,
                 environment,
                 server_id,
                 idrac_server_conf,
                 data_server_conf):
        """
        Constructor: create an instance of IDRAC8GUICollector class.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param server_id: Server identifier
            :type server_id: string

            :param idrac_server_conf: Dictionnatry containing IDRAC
                                      connectivity settings
            :type server_base_url: dictionary
            {
                "base_url": "IDRAC base URL. Ex.: https://localhost:443",
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
        self.idrac_server_conf = idrac_server_conf
        self.environment = environment
        if idrac_server_conf["user"] != "" and\
           idrac_server_conf["pass"] != "":
            self.pod_auth = (idrac_server_conf["user"],
                             idrac_server_conf["pass"])
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
        """Get Power value form IDRAC."""
        power = None
        rqt_url = self.idrac_server_conf["base_url"]
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
            log_msg = "Can't get power from IDRAC at "
            log_msg += self.idrac_server_conf["base_url"]
            self.log.error(log_msg)
            self.log.debug(response.text)
            raise Exception(log_msg)
        return power

    def login(self):
        """Get session_key from IDRAC."""
        rqt_url = self.idrac_server_conf["base_url"]
        rqt_url += "/data/login"
        payload = ("user=" + self.idrac_server_conf["user"] +
                   "&password=" + self.idrac_server_conf["pass"])
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
            self.log.debug("SID=" + session_id)
            return {"session_id": session_id, "ST2": url_parts[1]}
        else:
            log_msg = "Can't connect IDRAC at "
            log_msg += self.idrac_server_conf["base_url"]
            self.log.error(log_msg)
            self.log.debug(response.text)
            raise Exception(log_msg)

    def logout(self, session_id):
        """Logout from IDRAC."""
        rqt_url = self.idrac_server_conf["base_url"]
        rqt_url += "/data/logout"
        cookies = {
            "-http-session-": session_id
        }
        try:
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
        self.log.debug("Logged out")

    def run(self):
        """Thread main code."""
        self.running = True

        # Iterate for ever, or near....
        while self.running:

            try:
                session = None
                session = self.login()
                power = self.get_power(session)
                self.logout(session["session_id"])

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
                if session is not None:
                    self.logout(session["session_id"])
                err_text = sys.exc_info()[0]
                log_msg = "Error while trying to connect server {} ({}) \
                          for power query: {}"
                log_msg = log_msg.format(
                    self.server_id,
                    self.idrac_server_conf["base_url"],
                    err_text
                )
                self.log.debug(traceback.format_exc())
                self.log.error(err_text)

            time.sleep(self.idrac_server_conf["polling_interval"])

        log_msg = "Thread for server {} is teminated".format(self.server_id)
        self.log.debug(log_msg)
