# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Module Name : terraHouat  power recording  daemon
# Version : 1.1
#
# Copyright © 2019 Orange
# This software is distributed under the Apache 2 license
# <http://www.apache.org/licenses/LICENSE-2.0.html>
#
# -------------------------------------------------------
# File Name   : CSVFTPCollector.py
#
# Created     : 2019-04
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Collect data with rpi-monitor
# -------------------------------------------------------
# History     :
# 1.0.0 - 2019-05-15 : Release of the file
#

# Assume that rpimonitor is installed and running on collected remote box
# see: https://github.com/XavierBerger/RPi-Monitor

"""Collect RPI status data repimonitor."""
import json
import logging
import requests

from utils.collector import SensorsCollector


class RPIMONCollector(SensorsCollector):
    """Collect power consumption FTP protocol."""

    type = "rpimon"
    ftp_client = None

    _units = {
        "sdcard_boot_used": "Mo",
        "cpu_frequency": "MHz",
        "cpu_voltage": "V",
        "load15": "U-Ref",
        "uptime": "s",
        "load1": "U-Ref",
        "soc_temp": "deg. C",
        "sdcard_root_used": "Mo",
        "swap_used": "Mo",
        "load5": "U-Ref",
        "memory_free": "Mo",
        "memory_available": "Mo",
    }

    def get_sensors(self):
        """Get data from remote ftp compliant device."""

        result = []

        rpi_url = "http://" + self.server_conf["host"] + "/dynamic.json"
        resp = requests.get(
            rpi_url
        )
        if resp.status_code != 200:
            return result
        else:
            data = json.loads(resp.text)
            for key in data:
                if key in self._units:
                    result.append(
                        {
                            "sensor": key,
                            "unit": self._units[key],
                            "value": float(data[key]),
                        }
                    )
        return result


def main():
    """Execute basic test."""
    logging.basicConfig(level=logging.DEBUG)
    server_conf = {
        "host": "172.16.1.29:8888",
    }

    the_collector = RPIMONCollector(
        "FOO",
        "BAR",
        server_conf,
        "http://foo.bar.net"
    )

    the_collector.log.debug(the_collector.get_sensors())


if __name__ == "__main__":
    main()
