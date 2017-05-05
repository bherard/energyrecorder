# -*- coding: UTF-8 -*-
"""data-collector daemon main code."""
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
import traceback
import time
import signal
import sys
import yaml

from ilocollector import ILOCollector
from ipmicollector import IPMICollector
from redfishcollector import RedfishCollector


def signal_term_handler():
    """Sigterm signal handler."""
    for running_thread in SERVER_THREADS:
        msg = "Stopping thread for server {}".format(collector.server_id)
        LOG.info(msg)
        running_thread.stop()
    LOG.info("Please wait....")
    for running_thread in SERVER_THREADS:
        running_thread.join()
    LOG.info("Program terminated")


# Activate signal handler for SIGTERM
signal.signal(signal.SIGTERM, signal_term_handler)
# Create running thead list object
SERVER_THREADS = []
# Configure logging
logging.config.fileConfig("conf/collector-logging.conf")
LOG = logging.getLogger(__name__)

LOG.info("Server power consumption daemon is starting")
with open("conf/collector-settings.yaml", 'r') as stream:
    try:
        CONFIG = yaml.load(stream)
        # print(conf["PODS"])
    except yaml.YAMLError as exc:
        LOG.exception("Error while loading config")
        sys.exit()

for pod in CONFIG["PODS"]:
    log_msg = "Starting collector threads for pod {}"
    log_msg = log_msg.format(pod["environment"])
    LOG.info(log_msg)

    for server in pod["servers"]:
        log_msg = "\tStarting thread collector for server {}"
        log_msg = log_msg.format(server["id"])
        LOG.info(log_msg)
        if server["type"] == "ilo":
            ilo_server_conf = {
                "base_url": "https://{}".format(server["host"]),
                "user": server["user"],
                "pass": server["pass"],
                "polling_interval": server["polling_interval"]

            }
            collector = ILOCollector(pod["environment"],
                                     server["id"],
                                     ilo_server_conf,
                                     CONFIG["RECORDER_API_SERVER"])
        elif server["type"] == "redfish":
            ilo_server_conf = {
                "base_url": "https://{}".format(server["host"]),
                "user": server["user"],
                "pass": server["pass"],
                "polling_interval": server["polling_interval"]

            }
            # pylint: disable=redefined-variable-type
            collector = RedfishCollector(
                pod["environment"],
                server["id"],
                ilo_server_conf,
                CONFIG["RECORDER_API_SERVER"])
        elif server["type"] == "ipmi":
            ipmi_server_conf = {
                "host": server["host"],
                "user": server["user"],
                "pass": server["pass"],
                "polling_interval": server["polling_interval"]
            }

            # pylint: disable=redefined-variable-type
            collector = IPMICollector(pod["environment"],
                                      server["id"],
                                      ipmi_server_conf,
                                      CONFIG["RECORDER_API_SERVER"])

        SERVER_THREADS.append(collector)
        collector.start()

try:
    while True:
        # Wait for ever unless we receive a SIGTEM (see signal_term_handler)
        time.sleep(1)
except KeyboardInterrupt:
    signal_term_handler()
except SystemExit:
    pass
except Exception:  # pylint: disable=locally-disabled,broad-except
    MSG = "Unexpected error: {}".format(traceback.format_exc())
    LOG.error(MSG)
    signal_term_handler()

# Wait for the end of running threads
for thread in SERVER_THREADS:
    thread.join()
