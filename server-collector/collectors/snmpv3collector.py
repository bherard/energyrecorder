#!/usr/bin/python
# -*- coding: utf-8 -*-

# Collect data with SNMP v3 or Snmp v2

from utils.collector import SensorsCollector
from pysnmp.hlapi import *
import logging

class SnmpV3Collector(SensorsCollector):
    # Collect with Snmp V3 or Snmp V2 protocol

    type = "snmp"
    snmpV3_client = None

    def get_sensors(self):
        """Get data from remote snmp device."""

        result = []

        for sensor in self.server_conf["sensors"]:

            flag = self.server_conf["version"]  # snmpv3 or snmpv2

            if flag == 'v3':
                # Snmp v3
                for (errorIndication,
                     errorStatus,
                     errorIndex,
                     varBinds) in getCmd(SnmpEngine(),
                                         UsmUserData(userName=self.server_conf["username"],
                                                     authKey=self.server_conf["auth_secret"],
                                                     privKey=self.server_conf["privacy_secret"],
                                                     authProtocol=usmHMACSHAAuthProtocol,
                                                     privProtocol=usmAesCfb128Protocol),
                                         UdpTransportTarget((self.server_conf["host"], self.server_conf["port"])),
                                         ContextData(),
                                         ObjectType(ObjectIdentity(sensor["oid"])),
                                         lookupMib=False,
                                         lexicographicMode=False):

                    if errorIndication:
                        print(errorIndication)
                        break
                    elif errorStatus:
                        print('%s at %s' % (
                            errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                        break
                    else:
                        for varBind in varBinds:
                            print(' = '.join([x.prettyPrint() for x in varBind]))
                            try:
                                float(varBind[1])
                                result.append(
                                    {
                                        "sensor": sensor["name"],
                                        "unit": sensor["unit"],
                                        "value": float(varBind[1]),
                                    }
                                )
                            except ValueError:
                                if str(varBind[1]) == 'Unavailable':
                                    print ('skip : OID unknown')
                                else:
                                    # specific for boolean value
                                    if str(varBind[1]) == 'on' or str(varBind[1]) == 'true':
                                        result.append(
                                            {
                                                "sensor": sensor["name"],
                                                "unit": "boolean",
                                                "value": int(1),
                                            }
                                        )
                                    elif str(varBind[1]) == 'off' or str(varBind[1]) == 'false':
                                        result.append(
                                            {
                                                "sensor": sensor["name"],
                                                "unit": "boolean",
                                                "value": int(0),
                                            }
                                        )
                                    else:
                                        print ('skip : not numeric && not boolean')

            elif flag == 'v2': # example test on local Windows PC
                # Snmp V2
                for (errorIndication,
                     errorStatus,
                     errorIndex,
                     varBinds) in nextCmd(SnmpEngine(),
                                          CommunityData(self.server_conf["community"], mpModel=0),
                                          UdpTransportTarget((self.server_conf["host"], self.server_conf["port"])),
                                          ContextData(),
                                          ObjectType(ObjectIdentity(sensor["oid"])),
                                          lookupMib=False,
                                          lexicographicMode=False):

                    if errorIndication:
                        print(errorIndication)
                        break
                    elif errorStatus:
                        print('%s at %s' % (
                            errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                        break
                    else:
                        for varBind in varBinds:
                            print(' = '.join([x.prettyPrint() for x in varBind]))
                            try:
                                float(varBind[1])
                                result.append(
                                    {
                                        "sensor": sensor["name"],
                                        "unit": sensor["unit"],
                                        "value": float(varBind[1]),
                                    }
                                )
                            except ValueError:
                                if str(varBind[1]) == 'Unavailable':
                                    print ('skip : OID unknown')
                                else:
                                    print ('skip : not numeric')
        return result

def main():

    # Get Snmp data
    logging.basicConfig(level=logging.DEBUG)
    server_conf = {
        "host": SensorsCollector.server_conf["host"],
        "port": int(SensorsCollector.server_conf["port"]),
        "community": SensorsCollector.server_conf["community"],
        "type": SensorsCollector.server_conf["type"],
        "version": SensorsCollector.server_conf["version"],
        "sensors": SensorsCollector.server_conf["sensors"],
        "username": SensorsCollector.server_conf["username"],
        "auth_protocole": SensorsCollector.server_conf["auth_protocole"],
        "auth_secret": SensorsCollector.server_conf["auth_secret"],
        "privacy_protocole": SensorsCollector.server_conf["privacy_protocole"],
        "privacy_secret": SensorsCollector.server_conf["privacy_secret"]
    }

    the_collector = SnmpV3Collector(
        "FOO",
        "BAR",
        server_conf,
        "http://foo.bar.net"
    )

    the_collector.log.debug(the_collector.get_sensors())

if __name__ == "__main__":
    main()
