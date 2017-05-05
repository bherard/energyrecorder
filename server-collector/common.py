# -*- coding: UTF-8 -*-
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
import traceback
import sys
import json
import urllib
import requests


class DataPoster(Thread):
    """Post data to recorder API."""

    def __init__(self,
                 data,
                 data_server):
        """
        Create a DataPoster class instance.

        Create an instance of DataPoster class.
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

            api_uri = self.data_server["base_url"] + "/resources/servers/"
            api_uri += urllib.quote_plus(self.data["sender"])
            self.log.info(api_uri)
            response = requests.post(api_uri + "/consumption",
                                     data=json.dumps(payload),
                                     auth=auth,
                                     headers={
                                         'content-type': 'application/json'
                                     })

            self.log.debug('Message forwarded to data aggregator')
            self.log.debug("data aggregator answer is:")
            self.log.debug(response.text)
        except Exception:  # pylint: disable=locally-disabled,broad-except
            self.log.error("Error while sendind data to data aggregator")
            traceback.print_exc(file=sys.stdout)
