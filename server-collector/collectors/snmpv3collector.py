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


    def _get_auth_protocol(self, protocol_name):
        """Get auth protocol (snmp lib) according to a name."""

        res = None
        if not protocol_name or protocol_name == "NONE":
            """No Authentication Protocol"""
            res = usmNoAuthProtocol
        elif protocol_name == "HMAC-MD5-96":
            """The HMAC-MD5-96 Digest Authentication Protocol (:RFC:`3414#section-6`)"""
            res = usmHMACMD5AuthProtocol
        elif protocol_name == "HMAC-SHA-96" \
                or protocol_name == "SHA-1" \
                or protocol_name == "SHA1" \
                or protocol_name == "SHA":
            """The HMAC-SHA-96 Digest Authentication Protocol AKA SHA-1 (:RFC:`3414#section-7`)"""
            res = usmHMACSHAAuthProtocol
        elif protocol_name == "HMAC-SHA-2-128":
            """The HMAC-SHA-2 Digest Authentication Protocols (:RFC:`7860`)"""
            res = usmHMAC128SHA224AuthProtocol
        elif protocol_name == "HMAC-SHA-2-256":
            """The HMAC-SHA-2 Digest Authentication Protocols (:RFC:`7860`)"""
            res = usmHMAC192SHA256AuthProtocol
        elif protocol_name == "HMAC-SHA-2-384":
            """The HMAC-SHA-2 Digest Authentication Protocols (:RFC:`7860`)"""
            res = usmHMAC256SHA384AuthProtocol
        elif protocol_name == "HMAC-SHA-2-512":
            """The HMAC-SHA-2 Digest Authentication Protocols (:RFC:`7860`)"""
            res = usmHMAC384SHA512AuthProtocol
        elif protocol_name == "NO-PRIVACY":
            """No Privacy Protocol"""
            res = usmNoPrivProtocol
        elif protocol_name == "CBC-DES":
            """The CBC-DES Symmetric Encryption Protocol (:RFC:`3414#section-8`)"""
            res = usmDESPrivProtocol
        elif protocol_name == "3DES-EDE":
            """The 3DES-EDE Symmetric Encryption Protocol (`draft-reeder-snmpv3-usm-3desede-00 <https:://tools.ietf.org/html/draft-reeder-snmpv3-usm-3desede-00#section-5>`_)"""
            res = usm3DESEDEPrivProtocol
        elif protocol_name == "CFB128-AES-128" or protocol_name == "AES":
            """The CFB128-AES-128 Symmetric Encryption Protocol (:RFC:`3826#section-3`)"""
            res = usmAesCfb128Protocol
        elif protocol_name == "CFB128-AES-192":
            """The CFB128-AES-192 Symmetric Encryption Protocol (`draft-blumenthal-aes-usm-04 <https:://tools.ietf.org/html/draft-blumenthal-aes-usm-04#section-3>`_) with Reeder key localization"""
            res = usmAesCfb192Protocol
        elif protocol_name == "CFB128-AES-256":
            """The CFB128-AES-256 Symmetric Encryption Protocol (`draft-blumenthal-aes-usm-04 <https:://tools.ietf.org/html/draft-blumenthal-aes-usm-04#section-3>`_) with Reeder key localization"""
            res = usmAesCfb256Protocol
        elif protocol_name == "CFB192-AES-BLU":
            """The CFB192-AES-BLUMENTAL Symmetric Encryption Protocol (`draft-blumenthal-aes-usm-04 <https:://tools.ietf.org/html/draft-blumenthal-aes-usm-04#section-3>`_)"""
            res = usmAesBlumenthalCfb192Protocol
        elif protocol_name == "CFB256-AES-BLU":
            """The CFB128-AES-256 Symmetric Encryption Protocol (`draft-blumenthal-aes-usm-04 <https:://tools.ietf.org/html/draft-blumenthal-aes-usm-04#section-3>`_)"""
            res = usmAesBlumenthalCfb256Protocol
        elif protocol_name == "PASS-PHRASE":
            """USM key material type - plain-text pass phrase (:RFC:`3414#section-2.6`)"""
            res = usmKeyTypePassphrase
        elif protocol_name == "MASTER-KEY":
            """USM key material type - hashed pass-phrase AKA master key (:RFC:`3414#section-2.6`)"""
            res = usmKeyTypeMaster
        elif protocol_name == "HASHED-PASS-PHRASE":
            """USM key material type - hashed pass-phrase hashed with Context SNMP Engine ID (:RFC:`3414#section-2.6`)"""
            res = usmKeyTypeLocalized
        else:
            raise Exception("Unsupported Auth pprotocol: %s", protocol_name)
        return res

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
                     varBinds) in getCmd(
                        SnmpEngine(),
                        UsmUserData(
                            userName=self.server_conf["username"],
                            authKey=self.server_conf["auth_secret"],
                            privKey=self.server_conf["privacy_secret"],
                            authProtocol=self._get_auth_protocol(self.server_conf["auth_protocole"]),
                            privProtocol=self._get_auth_protocol(self.server_conf["privacy_protocole"])
                        ),
                        UdpTransportTarget((self.server_conf["host"], self.server_conf["port"])),
                        ContextData(),
                        ObjectType(ObjectIdentity(sensor["oid"])),
                        lookupMib=False,
                        lexicographicMode=False
                ):

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
        "host": "10.0.254.123",
        "port": 161,
        "community": "snmp-community",
        "type": "snmp",
        "version": "v3",
        "sensors": [
            {
                "name": "Power DC input of the module",
                "oid": "1.3.6.1.4.1.12551.4.1.1.1.1.27",
                "unit": "w"
            }
        ],
        "username": "nrj4it",
        "auth_protocole": "SHA",
        "auth_secret": "gdmice2022",
        "privacy_protocole": "AES",
        "privacy_secret": "gdmice2022"
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