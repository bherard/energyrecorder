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

from datetime import datetime
import struct

#from pyModbusTCP.client import ModbusClient
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer, ModbusSocketFramer

from utils.collector import SensorsCollector


class ModBUSCollector(SensorsCollector):
    """Collect power consumption ModBUS protocol."""

    type = "modbus"
    modbus_client = None

    def pre_run(self):
        """Initialize modbus client before starting."""
        pass

    def _create_modbus_client(self):
        port = 502
        tcp_settings = self.server_conf["host"].split(":")
        host = tcp_settings[0]
        if len(tcp_settings) > 1:
            port = int(tcp_settings[1])

        framer = ModbusSocketFramer
        if "framer" in self.server_conf:
            if self.server_conf["framer"] == "RTU":
                framer = ModbusRtuFramer
            elif self.server_conf["framer"] == "SOCKET":
                framer=ModbusSocketFramer
        self.modbus_client = ModbusClient(
            host=host,
            port=port,
            auto_open=True,
            auto_close=True,
            framer=framer
        )

    def _get_data_size(self, data_type):
        """Return registyer size accordind to data type."""

        ret = 1
        if data_type in ["MBL", "MBF", "MBUL"]:
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
        elif data_type == "MBUL":
            ret = raw_val # red value is already unsigned 32b int
        elif data_type == "MBF":
            ret = struct.unpack(
                '>f',  # Unpack as 32b float
                struct.pack('>I', raw_val)  # Pack as unsigned 32b int
            )[0]
        else:
            raise Exception("Unsupported data type: " + data_type)

        return ret

    def get_sensors(self):
        """Get data from remote modbus compliant device."""

        result = []

        self._create_modbus_client()
        if self.modbus_client.connect():
            for sensor in self.server_conf["sensors"]:
                if "register_category" not in sensor:
                    sensor["register_category"] = "holding"
                if sensor["register_category"] == "holding":
                    if "device_unit" in sensor:
                        vals = self.modbus_client.read_holding_registers(
                            sensor["register_address"],
                            self._get_data_size(
                                sensor["register_type"]
                            ),
                            unit=sensor["device_unit"]
                        ).registers
                    else:
                        vals = self.modbus_client.read_holding_registers(
                            sensor["register_address"],
                            self._get_data_size(
                                sensor["register_type"]
                            )
                        ).registers
                elif sensor["register_category"] == "input":
                    if "device_unit" in sensor:
                        vals = self.modbus_client.read_input_registers(
                            sensor["register_address"],
                            self._get_data_size(
                                sensor["register_type"]
                            ),
                            unit=sensor["device_unit"]
                        ).registers
                    else:
                        vals = self.modbus_client.read_input_registers(
                            sensor["register_address"],
                            self._get_data_size(
                                sensor["register_type"]
                            )
                        ).registers
                else:
                    self.log.error(
                        "Unsupported register category: %s",
                        sensor["register_category"]
                    )
                if "register_order" in sensor and\
                sensor["register_order"] == "left":
                    vals = self._revert_list(vals)

                if not vals:
                    self.log.error(
                        "[%s] Unable to get data for %s",
                        self.name,
                        sensor
                    )
                else:
                    res_val = self._convert_to_type(
                        vals,
                        sensor["register_type"]
                    )
                    if "register_scaling" in sensor:
                        res_val *= sensor["register_scaling"]
                    result.append(
                        {
                            "sensor": sensor["name"],
                            "unit": sensor["unit"],
                            "value": res_val
                        }
                    )
            self.modbus_client.close()


        else:
            self.log.error(
                "[%s]: Unable to get data from '%s'",
                self.name,
                self.server_conf["host"]
            )

        return result


if __name__ == "__main__":
    import logging
    FORMAT = ('%(asctime)-15s %(threadName)-15s'
            ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
    logging.basicConfig(format=FORMAT)
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    server_conf = {
        "host": "10.0.254.124:502",
        "framer": "RTU",
        "sensors": [
            {
                "name": "Phase1",
                "unit": "V",
                "register_category": "holding",
                "register_address": 4096,
                "register_type": "MBUL",
                "register_scaling": 0.001,
            },
            {
                "name": "Phase2",
                "unit": "V",
                "register_category": "holding",
                "register_address": 4098,
                "register_type": "MBUL",
                "register_scaling": 0.001,
            },
            {
                "name": "Phase3",
                "unit": "V",
                "register_category": "holding",
                "register_address": 4100,
                "register_type": "MBUL",
                "register_scaling": 0.001,
            },
            {
                "name": "Active Power",
                "unit": "W",
                "register_category": "holding",
                "register_address": 4116,
                "register_type": "MBUL",
                "register_scaling": 0.01,
            },
            
            
            
            
        ]
    }

    s2_conf = {
        "host": "localhost:1502",
        "sensors": [
            {
                "name": "holding",
                "unit": "foo",
                "register_category": "holding",
                "register_address": 0,
                "register_type": "MBU",
                "register_scaling": 1,
            },
            {
                "name": "input",
                "unit": "foo",
                "register_category": "input",
                "register_address": 0,
                "register_type": "MBU",
                "register_scaling": 1,
            }

        ]
    }


    the_collector = ModBUSCollector(
        "FOO",
        "BAR",
        server_conf,
        "http://localhost:8080"    
    )
    the_collector.pre_run()
    print(the_collector.get_sensors())
