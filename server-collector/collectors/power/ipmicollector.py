# -*- coding: utf-8 -*-
"""Collect power comsumption vi IPMI protocol."""
# --------------------------------------------------------
# Module Name : terraHouat  power recording ILO daemon
# Version : 1.1
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
# 1.1.0 - 2018-10-26 : Add feature to synchronize polling of different threads
##
import traceback
import sys
import subprocess

from utils.collector import Collector


class IPMICollector(Collector):
    """Collect power consumption via IPMI protocol."""

    type = "ipmi"

    #
    # Dictionnary for known Manufacturer
    # and associated "sensor" keyword for Power.

    grammar = {
        "11": "Power Meter",                     # HP
        "20301": "Avg Power",                    # IBM
        "28458": "HSC Input Power",              # Nokia
        "10297": "BOARD_POWER",                  # Advantech
        "40092": "HSC Input Power",              # Lenovo
        "674": "Pwr Consumption",                # DELL
        "5771": "POWER_USAGE",    	             # CISCO
        "343": "PS.* Input Power",               # Intel
        "2011": "Power[0-9]+|Power  ",           # Huawei
        "19046": "Sys Power",                    # Lenovo
    }

    _sensors = None

    def get_manufacturer_id(self):
        """Get Manufacturer id from IPMI."""
        self.log.debug(
            "[%s]: Getting manufacturer for server %s",
            self.name,
            self.server_conf["host"]
        )
        server_def = self.server_conf["host"].split(":")
        server_addr = server_def[0]
        sys_cmd = (
            "ipmitool -I lanplus -H " +
            server_addr +
            " -U '" + self.pod_auth[0] + "'" +
            " -P '" + self.pod_auth[1] + "'" +
            " bmc info"
        )
        ipmi_data = subprocess.check_output(
            sys_cmd,
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        if "Manufacturer ID" in str(ipmi_data):
            m_id = subprocess.check_output(
                'echo "' + ipmi_data + '"' +
                "| grep 'Manufacturer ID'|" +
                "awk -F ':' '{print $2}'",
                shell=True,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            m_id = m_id.strip(' \t\n\r')
            return m_id

    def get_sensors(self, manufacturer):
        """Return Power sensors list."""
        self.log.debug(
            "[%s]: Getting sensors from manufacturer '%s'",
            self.name,
            manufacturer
        )
        self.log.debug(
            "[%s]: Manufacturer IPMI pattern is '%s'",
            self.name,
            self.grammar[manufacturer]
        )
        server_def = self.server_conf["host"].split(":")
        if len(server_def) > 1:
            bridge_cmd = " -t " + server_def[1]
        else:
            bridge_cmd = ""
        sys_cmd = ("ipmitool -I lanplus -H " +
                   server_def[0] +
                   bridge_cmd +
                   " -U '" + self.pod_auth[0] + "'"
                   " -P '" + self.pod_auth[1] + "'"
                   " sensor "
                   "| egrep '" + self.grammar[manufacturer] + "'"
                   "| awk -F '|' '{print $1}'")
        ipmi_sensors = subprocess.check_output(sys_cmd,
                                               shell=True,
                                               stderr=subprocess.STDOUT,
                                               universal_newlines=True)
        s_list = ipmi_sensors.rstrip().split("\n")
        result = []
        for val in s_list:
            sensor = val.rstrip()
            self.log.debug(
                "[%s]: \tFound sensor %s from manufacturer %s",
                self.name,
                sensor,
                manufacturer
            )
            result.append(sensor)
        return result

    def get_sensors_power(self, sensors):
        """Return power value from sensor reading."""
        power = 0
        server_def = self.server_conf["host"].split(":")
        if len(server_def) > 1:
            bridge_cmd = " -t " + server_def[1]
        else:
            bridge_cmd = ""

        for sensor in sensors:
            try:
                sys_cmd = (
                    "ipmitool -I lanplus -H " +
                    server_def[0] +
                    bridge_cmd +
                    " -U '" + self.pod_auth[0] + "'"
                    " -P '" + self.pod_auth[1] + "'"
                    " sensor reading '" +
                    sensor + "'"
                )
                ipmi_data = subprocess.check_output(
                    sys_cmd,
                    shell=True,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True)
                sys_cmd = ""
                sys_cmd += 'echo "' + ipmi_data + '"'
                sys_cmd += "|awk -F '|' '{print $2}'"

                str_power = subprocess.check_output(sys_cmd, shell=True)
                str_power = str_power.strip(' \t\n\r')
                if str_power != "":
                    sensor_power = int(float(str_power))
                    self.log.debug(
                        "[%s]: \tGot power '%s' from sensor '%s' for %s",
                        self.name,
                        sensor_power,
                        sensor,
                        server_def[0]
                    )
                    power += sensor_power
            except subprocess.CalledProcessError as exc:
                if exc.returncode == 1:
                    self.log.debug("[%s]: Wrong sensor: %s", self.name, sensor)
                    continue
                else:
                    self.log.error(
                        "[%s]: IPMI Error while trying to get Power data "
                        " (%s): rc=%d err=%s",
                        self.name,
                        server_def[0],
                        exc.returncode,
                        exc.output
                    )

        self.log.debug("[%s]: Global power is %d", self.name, power)
        return power

    def pre_run(self):
        """Thread main code."""

        manufacturer = self.get_manufacturer_id()
        if manufacturer not in self.grammar:
            self.log.error(
                "[%s]: Manufacturer ID %s not supported",
                self.name,
                manufacturer
            )
        else:
            self._sensors = self.get_sensors(manufacturer)
            self.log.debug("[%s]: Main thread is starting....", self.name)

    def get_power(self):
        """Get power with IPMI."""

        try:
            power = self.get_sensors_power(self._sensors)
            if power is not None:
                return power
            else:
                self.log.error(
                    "[%s]: Power consumption is not avaliable via IPMI",
                    self.name
                )
                return 0
        except subprocess.CalledProcessError as exc:
            self.log.error(
                "[%s]: IPMI Error while trying to get Power data: "
                "rc=%d err=%s",
                self.name,
                exc.returncode,
                exc.output
            )
        except Exception:  # pylint: disable=locally-disabled,broad-except
            server_def = self.server_conf["host"].split(":")
            server_addr = server_def[0]

            err_text = sys.exc_info()[0]
            self.log.debug("[%s]: %s", self.name, traceback.format_exc())

            self.log.error(
                "[%s]: Error while trying to connect server "
                "(%s) for power query: %s",
                self.name,
                server_addr,
                err_text
            )
