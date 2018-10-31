#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""data-collector daemon main code."""
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
import logging.config
import traceback
import time
import signal
import sys
import threading
from threading import Thread
import yaml

from ilocollector import ILOCollector
from ilo_gui_collector import ILOGUICollector
from idrac8_gui_collector import IDRAC8GUICollector
from intel_gui_collector import INTELGUICollector
from ibmc_gui_collector import IBMCGUICollector
from ipmicollector import IPMICollector
from redfishcollector import RedfishCollector


class Poller(Thread):
    """Execute synchronized polling opn a set of collectors."""

    def __init__(self, conf):
        """Initialize polling thread."""
        Thread.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.conf = conf
        self.running = False

    def stop(self):
        """Request stop on running thread."""
        self.running = False

    def run(self):
        self.running = True
        condition = self.conf["sync_condition"]

        for _collector in self.conf["collectors"]:
            _collector.start()

        while self.running:
            condition.acquire()
            condition.notify_all()
            condition.release()

            time.sleep(self.conf["polling_interval"])

        self.logger.debug("Stoping collectors for poller")
        for _collector in self.conf["collectors"]:
            _collector.stop()

        condition.acquire()
        condition.notify_all()
        condition.release()

        self.logger.debug("Waiting for collectors to stop")
        for _collector in self.conf["collectors"]:
            collector.join()
        self.logger.debug("Poller stoped")


def signal_term_handler():
    """Sigterm signal handler."""
    for running_thread in POLLERS:
        msg = "Stopping thread for poller"
        LOG.info(msg)
        running_thread.stop()
    LOG.info("Waiting for pollers to stop....")
    for running_thread in POLLERS:
        running_thread.join()
    LOG.info("Program terminated")


def get_collector(server, pod):
    """Get proper collector instance."""

    if server["type"] == "ilo":
        ilo_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"],
            "sync_condition": poller_conf["sync_condition"]

        }
        the_collector = ILOCollector(
            pod["environment"],
            server["id"],
            ilo_server_conf,
            CONFIG["RECORDER_API_SERVER"]
        )
    elif server["type"] == "ilo-gui":
        ilo_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"],
            "sync_condition": poller_conf["sync_condition"]

        }
        the_collector = ILOGUICollector(
            pod["environment"],
            server["id"],
            ilo_server_conf,
            CONFIG["RECORDER_API_SERVER"]
        )

    elif server["type"] == "idrac8-gui":
        idrac_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"],
            "sync_condition": poller_conf["sync_condition"]

        }
        the_collector = IDRAC8GUICollector(
            pod["environment"],
            server["id"],
            idrac_server_conf,
            CONFIG["RECORDER_API_SERVER"]
        )

    elif server["type"] == "intel-gui":
        intel_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"],
            "sync_condition": poller_conf["sync_condition"]

        }
        the_collector = INTELGUICollector(
            pod["environment"],
            server["id"],
            intel_server_conf,
            CONFIG["RECORDER_API_SERVER"]
        )

    elif server["type"] == "ibmc-gui":
        ibmc_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"],
            "sync_condition": poller_conf["sync_condition"]

        }
        the_collector = IBMCGUICollector(
            pod["environment"],
            server["id"],
            ibmc_server_conf,
            CONFIG["RECORDER_API_SERVER"]
        )

    elif server["type"] == "redfish":
        server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"],
            "sync_condition": poller_conf["sync_condition"]
        }
        the_collector = RedfishCollector(
            pod["environment"],
            server["id"],
            server_conf,
            CONFIG["RECORDER_API_SERVER"])
    elif server["type"] == "ipmi":
        ipmi_server_conf = {
            "host": server["host"],
            "user": server["user"],
            "pass": server["pass"],
            "sync_condition": poller_conf["sync_condition"]
        }

        the_collector = IPMICollector(
            pod["environment"],
            server["id"],
            ipmi_server_conf,
            CONFIG["RECORDER_API_SERVER"]
        )
    else:
        msg = "Unsupported power collect method: {}"
        msg += msg.format(server["type"])
        raise Exception(msg)

    return the_collector


# Activate signal handler for SIGTERM
signal.signal(signal.SIGTERM, signal_term_handler)

# Create a list of active pollers
POLLERS = []

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

for a_pod in CONFIG["PODS"]:
    LOG.info(
        "Loading configuration for pod %s",
        a_pod["environment"]
    )

    if "polling_interval" not in a_pod:
        polling_interval = 10
        LOG.warn(
            "\n\n*******************************\n\n"
            "\"polling_interval\" is not set in PODS definition yaml file "
            "(at environment level) using default setting: %ds "
            "\n\n*******************************\n\n",
            polling_interval
        )
    else:
        polling_interval = a_pod["polling_interval"]

    poller_conf = {
        "polling_interval": polling_interval,
        "sync_condition": threading.Condition(),
        "collectors": [],
        "active": True
    }

    if "active" in a_pod:
        poller_conf["active"] = a_pod["active"]

    if poller_conf["active"]:
        for srv in a_pod["servers"]:
            if "active" not in srv or srv["active"]:
                collector = get_collector(srv, a_pod)
                poller_conf["collectors"].append(collector)
            else:
                LOG.info(
                    "Server %s is not active: skipping",
                    srv["id"]
                )

        poller = Poller(poller_conf)
        POLLERS.append(poller)

        LOG.info(
            "Starting poller threads for pod %s",
            a_pod["environment"]
        )
        poller.start()
    else:
        LOG.info(
            "Environment %s is not active: skipping",
            a_pod["environment"]
        )

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    signal_term_handler()
except SystemExit:
    pass
except Exception:  # pylint: disable=locally-disabled,broad-except
    MSG = "Unexpected error: {}".format(traceback.format_exc())
    LOG.error(MSG)
    signal_term_handler()
