# -*- coding: UTF-8 -*-
"""Collect power comsumption vi IPMI protocol."""
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
# File Name   : iloCollector.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Daemon implementation
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
##
import logging.config
import time
import traceback
import sys
import subprocess

from threading import Thread
from common import DataPoster


class IPMICollector(Thread):
    """Collect power consumption via IPMI protocol."""

    #
    # Dictionnary for known Manufacturer
    # and associated "sensor" keyword for Power.

    grammar = {
        "11": "PwrMeter Output",     # HP
        "20301": "Avg Power",        # IBM
        "28458": "HSC Input Power",  # Nokia
        "10297": "BOARD_POWER",      # Advantech
        "40092": "HSC Input Power",  # Lenovo
        "674": "Pwr Consumption",    # DELL
    }

    def __init__(self,
                 environment,
                 server_id,
                 ipmi_server_conf,
                 data_server_conf):
        """
        Constructor: create an instance of IPMICollector class.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param server_id: Server identifier
            :type server_id: string

            :param ipmi_server_conf: Dictionnatry containing ILO API
                                     connectivity settings
            :type server_base_url: dictionary
            {
                "host": "ILO API base URL. Ex.: localhost",
                "user": Basic authentication user,
                "pass": Basic authentication password
                "polling_interval": Polling interval duration
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
        self.ipmi_server_conf = ipmi_server_conf
        self.environment = environment
        if ipmi_server_conf["user"] != "" and\
           ipmi_server_conf["pass"] != "":
            self.pod_auth = (
                ipmi_server_conf["user"],
                ipmi_server_conf["pass"]
            )
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

    def get_manufacturer_id(self):
        """Get Manufacturer id from IPMI."""
        try:
            server_def = self.ipmi_server_conf["host"].split(":")
            server_addr = server_def[0]
            ipmi_data = subprocess.check_output("ipmitool -I lanplus -H " +
                                                server_addr +
                                                " -U " + self.pod_auth[0] +
                                                " -P " + self.pod_auth[1] +
                                                " bmc info",
                                                shell=True,
                                                stderr=subprocess.STDOUT,
                                                universal_newlines=True)
            if "Manufacturer ID" in ipmi_data:
                m_id = subprocess.check_output('echo "' + ipmi_data + '"' +
                                               "| grep 'Manufacturer ID'|" +
                                               "awk -F ':' '{print $2}'",
                                               shell=True,
                                               stderr=subprocess.STDOUT,
                                               universal_newlines=True)
                m_id = m_id.strip(' \t\n\r')
                return m_id
        except subprocess.CalledProcessError as exc:
            log_msg = "IPMI Error: rc={} err={}".format(exc.returncode,
                                                        exc.output)
            self.log.error(log_msg)
            return "none"

    def run(self):
        """Thread main code."""
        self.running = True

        manufacturer = self.get_manufacturer_id()
        if manufacturer not in self.grammar:
            log_msg = "Manufacturer ID {} not supported".format(manufacturer)
            self.log.error(log_msg)
            self.running = False
        while self.running:

            try:
                server_def = self.ipmi_server_conf["host"].split(":")
                if len(server_def) > 1:
                    bridge_cmd = " -t " + server_def[1]
                else:
                    bridge_cmd = ""

                ipmi_data = subprocess.check_output("ipmitool -I lanplus -H " +
                                                    server_def[0] +
                                                    bridge_cmd +
                                                    " -U " + self.pod_auth[0] +
                                                    " -P " + self.pod_auth[1] +
                                                    " sensor",
                                                    shell=True,
                                                    stderr=subprocess.STDOUT,
                                                    universal_newlines=True)
                if self.grammar[manufacturer] in ipmi_data:
                    sys_cmd = ""
                    sys_cmd += 'echo "' + ipmi_data + '"'
                    sys_cmd += "| grep '" + self.grammar[manufacturer]
                    sys_cmd += "'|awk -F '|' '{print $2}'"

                    str_power = subprocess.check_output(sys_cmd, shell=True)
                    str_power = str_power.strip(' \t\n\r')
                    self.log.debug(str_power)

                    power = int(float(str_power))

                    cur_time = time.time()
                    data_time = int(cur_time) * 1000000000

                    self.log.debug("IPMI POWER=" + str(power))

                    data = {
                        "environment": self.environment,
                        "sender": self.server_id,
                        "power": power,
                        "data_time": data_time
                    }
                    data_poster = DataPoster(data,
                                             self.data_server_conf)
                    data_poster.start()

            except ValueError:
                log_msg = "Power consumption is not avaliable via IPMI"
                self.log.error(log_msg)
            except subprocess.CalledProcessError as exc:
                log_msg = "IPMI Error while trying to get Power data: "
                log_msg += "rc={} err={}"
                log_msg = log_msg.format(exc.returncode, exc.output)
                self.log.error(log_msg)
            except Exception:  # pylint: disable=locally-disabled,broad-except
                err_text = sys.exc_info()[0]
                self.log.debug(traceback.format_exc())

                log_msg = "Error while trying to connect server "
                log_msg += "{} ({}) for power query: {}"
                log_msg = log_msg.format(
                    self.server_id, self.server_addr, err_text)

                self.log.error(log_msg)
                self.running = False

            time.sleep(self.ipmi_server_conf["polling_interval"])
        log_msg = "Thread for server {} is teminated".format(self.server_id)
        self.log.debug(log_msg)
