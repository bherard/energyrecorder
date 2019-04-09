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
# File Name   : ModBUSCollector.py
#
# Created     : 2019-04
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Colelct data with ModBUS
# -------------------------------------------------------
# History     :
# 1.0.0 - 2019-04-08 : Release of the file
#

"""Collect power data with ModBUS."""

import struct

from pyModbusTCP.client import ModbusClient
from collector import Collector


class ModBUSCollector(Collector):
    """Collect power consumption ModBUS protocol."""

    type = "modbus"
    modbus_client = None

    def pre_run(self):
        """Initialize modbus client before starting."""

        port = 502
        tcp_settings = self.server_conf["host"].split(":")
        host = tcp_settings[0]
        if len(tcp_settings) > 1:
            port = int(tcp_settings[1])

        self.modbus_client = ModbusClient(
            host=host,
            port=port,
            auto_open=True,
            auto_close=True
        )

    def _get_data_size(self, data_type):
        """Return registyer size accordind to data type."""

        ret = 1
        if data_type in ["MBL", "MBF"]:
            ret = 2
        else:
            ret = 1

        return ret

    def _revert_list(self, a_list):
        """Reverse a list."""

        ret = []
        for item in reversed(a_list):
            ret.append(item)
        return ret

    def _convert_to_type(self, vals, data_type):
        """
        Return real value from 16b vals and data_type.


        Convert via bytes serialization/deserialization
        Values comming from ModBUS are WORDS (16 bits) and
        considered here as unsigned integers
        see https://docs.python.org/3/library/struct.html
        """

        # First concatenate red values as a "16b multiple" assuming that
        # WORDS are right ordered in vals (lowest WORD at right)
        raw_val = 0
        for val in vals:
            raw_val <<= 16
            raw_val += val

        # Convertion itself
        if data_type == "MBI":
            ret = struct.unpack(
                '>h',  # Unpack as 16b signed int
                struct.pack('>H', raw_val)  # Pack as unsigned 16b int
            )[0]
        elif data_type == "MBU":
            ret = raw_val  # red value is already unsigned 16b int
        elif data_type == "MBL":
            ret = struct.unpack(
                '>i',  # unpack as signed 32b int
                struct.pack('>I', raw_val)  # Pack as unsigned 32b int
            )[0]
        elif data_type == "MBF":
            ret = struct.unpack(
                '>f',  # Unpack as 32b float
                struct.pack('>I', raw_val)  # Pack as unsigned 32b int
            )[0]
        else:
            raise Exception("Unsupported data type: " + data_type)

        return ret

    def get_power(self):
        """Get data from remote modbus compliant device."""

        result = None

        if self.modbus_client.open():
            vals = self.modbus_client.read_holding_registers(
                self.server_conf["register_address"],
                self._get_data_size(
                    self.server_conf["register_type"]
                )
            )
            self.modbus_client.close()

            if "register_order" in self.server_conf and\
               self.server_conf["register_order"] == "left":
                vals = self._revert_list(vals)

            result = self._convert_to_type(
                vals,
                self.server_conf["register_type"]
            )

        else:
            self.log.error(
                "[%s]: Unable to get data from '%s'",
                self.name,
                self.server_conf["host"]
            )

        return result
