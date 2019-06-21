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
#     Collect data with CSV via FTP
# -------------------------------------------------------
# History     :
# 1.0.0 - 2019-04-08 : Release of the file
#

# Assume that collected CSV files have the following structure:
#   1st column: datetime of measurement with format:
#       YYYY/MM/DD HH:MI:SS.ssss
#   2nd column: TIMEZONE for measurement datetime with format
#       HHMI offset from UTC Ex. +0200, -0500
#       or
#       +HH:MI offset from UTC Ex. +02:00, -05:00
#       or
#       Z for UTC
#       or
#       Valid full timezone name ex Europe/Paris
#       or
#       With any other value, will use host TZ
#   1st line: Sensors name and unit in format:
#       sensor name (Unit)
#       Ex: "Timestamp","TZ","U_bat_1 (V)","I_load_1 (A)","I_bat_1 (A)"
#   Following lines: data as float
#       Ex: 2017/07/17 09:04:00.000,n,56.370628,0.106086,22.658

"""Collect power data with CSV via FTP."""
import datetime
import logging
import os
import re
import time
from ftplib import FTP

import pytz

from utils.collector import SensorsCollector


class CSVFTPCollector(SensorsCollector):
    """Collect power consumption FTP protocol."""

    type = "csvftp"
    ftp_client = None

    def __init__(self, environment, server_id, server_conf, data_server_conf):
        super().__init__(
            environment, server_id, server_conf, data_server_conf
        )
        if "file_filter" not in self.server_conf:
            self.server_conf["file_filter"] = "*"
        if "encoding" not in self.server_conf:
            self.server_conf["encoding"] = "utf8"

    def _get_headers_def(self, def_line):
        """Return a list of sensors definition from CVS cols. def line."""

        headers = []

        cols = def_line.replace('"', "").split(",")
        cols.pop(0)  # Remove "Timestamp" col
        cols.pop(0)  # Remove "TZ" col

        for col in cols:  # format: "sensor_name or desc (Unit)"
            sensor = col.split(" (")

            if len(sensor) > 1:
                unit = sensor[1].replace(")", "")
            else:
                unit = "n/d"
            headers.append(
                {
                    "sensor": sensor[0],
                    "unit": unit
                }
            )
        return headers

    def _get_timestamp(self, str_datetime, str_tz):
        """
            Return unix timestamp (in nano sec) from:
                - data time in YYYY/MM/DD HH:MI:SS.nnn format
                - timezone
                    Time zone may be of the form:
                        - ISO offest from UTC (ex.: +02:00)
                        - Python offest from UTC (ex.: +0200)
                        - Full name (ex.: Europe/Paris)
                        - "Z" (zulu i.e UTC)

                Note: date may also be YYYY-MM-DD
        """

        str_datetime = str_datetime.replace("-", "/").replace('"', "")
        if re.match(r"^[+|-][0-2][0-3]:?[0-5][0-9]|Z$", str_tz):
            # TZ is offet from UTC with DST like +0200  or "Z"
            # (eventually convert [+|-]HH:MI form to [+|-]HHMI or Z to +0000
            # whitch is TZ format supported by python "%z" date formatter)
            str_tz = str_tz.replace(":", "").replace("Z", "+0000")
            fmt = "%Y/%m/%d %H:%M:%S.%f%z"
        elif re.match(r"^[A-Z|a-z]*/[A-Z|a-z]*", str_tz):
            # TZ is full name like Europe/Paris

            # Get timezone offet from UTC (wverify_certith DST) form
            # date and TZ name
            data_dt = datetime.datetime.strptime(
                str_datetime,
                "%Y/%m/%d %H:%M:%S.%f"
            )
            str_tz = pytz.timezone(
                str_tz
            ).localize(
                data_dt
            ).strftime(
                "%z"
            )

            fmt = "%Y/%m/%d %H:%M:%S.%f%z"

        else:
            # str_tz is not a valid TZ
            # and not TZ specified for connector
            # Will use host timezone
            fmt = "%Y/%m/%d %H:%M:%S.%f"
            str_tz = ""

        if not re.match(r".*\.[0-9]*$", str_datetime):
            # datetime don't have millis. Add arbitrary
            millis = int(round(time.time() * 1000))
            str_datetime = str_datetime + "." + str(millis % 1000)

        res = int(
            datetime.datetime.strptime(
                str_datetime + str_tz,
                fmt
            ).timestamp()) * 1000000000

        return res

    def _load_data_from_ftp_file(self, filename, ftp_client):
        """Load data from file on ftp server in an array."""

        self.log.debug(
            "[%s]: Getting data from file %s",
            self.name,
            filename
        )
        data = []
        try:
            tmp_filename = '/tmp/' + str(time.time()) + '_' + filename
            fout = open(tmp_filename, 'wb')
            ftp_client.retrbinary('RETR ' + filename, fout.write)
            fout.close()
            fin = open(tmp_filename, "rb")
            for line in fin:
                data.append(line)
            fin.close()
        except Exception:  # pylint: disable=broad-except
            self.log.exception(
                "[%s] Error while getting data from %s",
                self.name,
                filename
            )
        os.remove(tmp_filename)
        self.log.debug(
            "[%s]: Data loaded from file %s",
            self.name,
            filename
        )

        return data

    def _get_decoded_line(self, line):
        """Get line from CSV data file as decoded string."""
        return line.decode(
            self.server_conf["encoding"]
        ).replace(
            "\r\n",
            "\n"
        ).split("\n")[0]

    def _get_file_data(self, filename, ftp_client):
        """Get data from filename."""

        data = []
        res = []

        self.log.info(
            "[%s]: Ready to process file %s",
            self.name,
            filename
        )
        data = self._load_data_from_ftp_file(filename, ftp_client)
        if data == []:
            return res

        hdr_line = self._get_decoded_line(data[0])

        headers = self._get_headers_def(hdr_line)
        data.pop(0)

        for line in data:
            if line != "":
                line = self._get_decoded_line(line)
                try:
                    cols = line.split(',')
                    if "tz" in self.server_conf:
                        str_tz = self.server_conf["tz"]
                    else:
                        str_tz = cols[1]
                    timestamp = self._get_timestamp(cols[0], str_tz)
                    cols.pop(0)
                    cols.pop(0)
                    i = 0
                    while i < len(cols):
                        try:
                            res.append(
                                {
                                    "sensor": headers[i]["sensor"],
                                    "unit": headers[i]["unit"],
                                    "value": float(cols[i]),
                                    "time": timestamp
                                }
                            )
                        except ValueError:
                            self.log.debug(
                                "'%s' is not a valid value", cols[i]
                            )
                        i += 1
                except Exception as exc:  # pylint: disable=broad-except
                    self.log.warning(
                        "Can not parse line %s (%s): Skipping...",
                        line,
                        exc
                    )

        return res

    def _get_ftp_connection(self):
        """Connect to FTP server and switch to data collect directory."""

        ftp_client = FTP(self.server_conf["host"], timeout=20)

        ftp_client.login(
            self.server_conf["user"],
            self.server_conf["pass"]
        )
        ftp_client.cwd(self.server_conf["root_dir"])
        self.log.debug(
            "[%s]: Connected to FTP server at %s in directory %s",
            self.name,
            self.server_conf["host"],
            self.server_conf["root_dir"]
        )

        return ftp_client

    def get_sensors(self):
        """Get data from remote ftp compliant device."""

        result = []
        ftp_client = self._get_ftp_connection()

        files = []
        try:
            for filename in ftp_client.nlst(self.server_conf["file_filter"]):
                result += self._get_file_data(filename, ftp_client)
                files.append(filename)

                if "max_files" in self.server_conf and \
                   len(files) >= self.server_conf["max_files"]:
                    self.log.warning(
                        "[%s] File count exceed %d: breaking",
                        self.name,
                        self.server_conf["max_files"]
                    )
                    break
            self.on_send_ok(self.remove_files, files)
        finally:
            ftp_client.close()
        self.log.info(
            "[%s] Got %d data from %d files: ready to send",
            self.name,
            len(result),
            len(files)
        )

        return result

    def remove_files(self, files):
        """Remove files from remote FTP server."""

        if files != [] and \
           "purge" in self.server_conf and\
           self.server_conf["purge"]:

            self.log.info("[%s] Removing %s", self.name, files)
            try:
                ftp_client = self._get_ftp_connection()

                for filename in files:
                    self.log.debug(
                        "[%s] DELE %s",
                        self.name,
                        filename
                    )
                    ftp_client.delete(filename)
            except Exception as exc:  # pylint: disable=broad-except
                self.log.warning(
                    "[%s] Error while deleteing file from FTP server (%s)",
                    self.name,
                    exc
                )
            finally:
                ftp_client.close()


def main():
    """Execute basic test."""
    logging.basicConfig(level=logging.DEBUG)

    ftp_server_conf = {
        "host": "localhost",
        "user": "foo",
        "pass": "bar",
        "root_dir": "/home/foo/ftpdir/brian",
        "purge": False,
        "file_filter": "*csv",
        "encoding": "utf8"
    }

    the_collector = CSVFTPCollector(
        "FOO",
        "BAR",
        ftp_server_conf,
        "http://foo.bar.net"
    )

    the_collector.log.info(the_collector.get_sensors())


if __name__ == "__main__":
    main()
