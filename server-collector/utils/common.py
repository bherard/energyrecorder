# -*- coding: utf-8 -*-
"""Common classes and tools for server-collector."""
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
# File Name   : common.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Common classes
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
##

from threading import Thread
import logging.config
import json
import urllib
import requests


class PowerPoster(Thread):
    """Post power data to recorder API."""

    def __init__(self,
                 data,
                 data_server):
        """
        Create a PowerPoster class instance.

        Create an instance of PowerPoster class.
            :param data: Dictionary containing data to post
            :type data: dictionary
            {
                "environment": "Environment on witch power is collected",
                "sender": "Power measurement related server identifier",
                "power": power value (int),
                "data_time": Timestamp (in ns) of measurement
            }
            :param data_server: Dictionary containing data server
                                connectivity settings
            :type data_server: dictionary
            {
                "base_url": "Recorder API base URL",
                "user": Basic authentication user,
                "pass": Basic authentication password
            }

        """
        self.log = logging.getLogger(__name__)
        Thread.__init__(self)
        self.data = data
        self.data_server = data_server

    def run(self):
        """Thread main code."""
        # Send the message to data aggregation server
        # Creating payload for HTTP Post message
        payload = {'power': self.data["power"],
                   'time': self.data["data_time"],
                   'environment': self.data["environment"]}
        try:
            if self.data_server["user"] != "" and\
               self.data_server["pass"] != "":
                auth = (
                    self.data_server["user"],
                    self.data_server["pass"]
                )
            else:
                auth = None

            if "verify_cert" in self.data_server:
                verify_cert = self.data_server["verify_cert"]
            else:
                verify_cert = True

            connect_timeout = 10
            read_timeout = 300

            if "timeout" in self.data_server:
                read_timeout = self.data_server["timeout"]

            api_uri = self.data_server["base_url"] + "/resources/servers/"
            api_uri += urllib.parse.quote(self.data["sender"])
            self.log.info("[%s]: %s", self.name, api_uri)
            response = requests.post(
                api_uri + "/consumption",
                data=json.dumps(payload),
                auth=auth,
                headers={
                    'content-type': 'application/json'
                },
                verify=verify_cert,
                timeout=(connect_timeout, read_timeout)
            )

            self.log.debug(
                '[%s]: Message forwarded to data aggregator',
                self.name
            )
            self.log.debug("[%s]: data aggregator answer is:", self.name)
            self.log.debug("[%s]: %s", self.name, response.text)
            if response.status_code == 200:
                self.log.info(
                    "[%s]: Message successfully forwarded "
                    "to data aggregator':",
                    self.name
                )

        except Exception:  # pylint: disable=locally-disabled,broad-except
            self.log.exception(
                "[%s]: Error while sendind data to data aggregator",
                self.name
            )


class SensorsPoster(Thread):
    """Post sensors data to recorder API."""

    def __init__(self,
                 data,
                 data_server):
        """
        Create a SensorsPoster class instance.

        Create an instance of SensorsPoster class.
            :param data: Dictionary containing data to post
            :type data: dictionary
            {
                "environment": "Environment on witch power is collected",
                "sender": "Power measurement related server identifier",
                "measurments": list,
                "data_time": Timestamp (in ns) of measurement
            }
            :param data_server: Dictionary containing data server
                                connectivity settings
            :type data_server: dictionary
            {
                "base_url": "Recorder API base URL",
                "user": Basic authentication user,
                "pass": Basic authentication password
            }

        """
        self.log = logging.getLogger(__name__)
        Thread.__init__(self)
        self.data = data
        self.data_server = data_server
        self._on_send_ok = {}
        self._chunk_len = 10000

    def on_send_ok(self, func, *args):
        """
            Register function (with args) to trigger on successfull data send.
        """
        self._on_send_ok["func"] = func
        self._on_send_ok["args"] = args

    def run(self):
        """Thread main code."""
        # Send the message to data aggregation server
        # Creating payload for HTTP Post message
        self.log.debug("Thread name = %s ", self.name)
        payload = {'measurements': self.data["measurements"],
                   'time': self.data["data_time"],
                   'environment': self.data["environment"]}
        try:
            if self.data_server["user"] != "" and\
               self.data_server["pass"] != "":
                auth = (
                    self.data_server["user"],
                    self.data_server["pass"]
                )
            else:
                auth = None

            if "verify_cert" in self.data_server:
                verify_cert = self.data_server["verify_cert"]
            else:
                verify_cert = True

            connect_timeout = 10
            read_timeout = 300
            if "timeout" in self.data_server:
                read_timeout = self.data_server["timeout"]

            api_uri = self.data_server["base_url"] + "/resources/equipments/"
            # api_uri += urllib.parse.quote(self.data["sender"])
            api_uri += self.data["sender"] # Fix sending to recorder
            api_uri += "/measurements"
            self.log.info("[%s]: %s", self.name, api_uri)

            chunk_payload = {
                "environment": payload["environment"],
                "time": payload["time"],
                "measurements": []
            }
            item_idx = 0
            while item_idx < len(payload["measurements"]):
                chunk_data = []
                while item_idx < len(payload["measurements"]) and \
                        len(chunk_data) < self._chunk_len:
                    chunk_data.append(payload["measurements"][item_idx])
                    item_idx += 1
                chunk_payload["measurements"] = chunk_data
                response = requests.post(
                    api_uri,
                    data=json.dumps(chunk_payload),
                    auth=auth,
                    headers={
                        'content-type': 'application/json'
                    },
                    verify=verify_cert,
                    timeout=(connect_timeout, read_timeout)
                )

                self.log.debug(
                    '[%s]: chunk forwarded to data aggregator',
                    self.name
                )
                self.log.debug("[%s]: data aggregator answer is:", self.name)
                self.log.debug("[%s]: %s", self.name, response.text)
                if response.status_code != 200:
                    raise Exception(response.text)

            self.log.info(
                "[%s]: Message successfully forwarded "
                "to data aggregator':",
                self.name
            )
            jresp = json.loads(response.text)
            if jresp["status"] == "OK":
                if "func" in self._on_send_ok:
                    self._on_send_ok["func"](
                        *self._on_send_ok["args"]
                    )
        except Exception:  # pylint: disable=locally-disabled,broad-except
            self.log.exception(
                "[%s]: Error while sendind data to data aggregator",
                self.name
            )
