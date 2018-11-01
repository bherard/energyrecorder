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


# Create a list of active pollers
POLLERS = []


class Poller(Thread):
    """Execute synchronized polling opn a set of collectors."""

    def __init__(self, conf):
        """Initialize polling thread."""
        Thread.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.conf = conf
        self.running = False
        self.condition = threading.Condition()
        if self.conf["polling_interval"] <= 0:
            self.conf["polling_interval"] = 0.1

    def notity_collectors(self):
        """Notify collectors to execute power reading."""
        self.condition.acquire()
        self.condition.notify_all()
        self.condition.release()

    def stop(self):
        """Request stop on running thread."""
        self.running = False

    def _interruptible_sleep(self, duration):
        """Execute fragmeted sleep to be interruptible by signals."""
        if duration > 0.1:
            sleep_duration = 0.1
        else:
            sleep_duration = duration
        spend_time = 0
        while spend_time <= duration and self.running:
            time.sleep(sleep_duration)
            spend_time += sleep_duration

    def run(self):
        self.running = True

        # Start all collect threads
        for _collector in self.conf["collectors"]:
            _collector.condition = self.condition
            _collector.start()

        # Ensure colelctors are ready (i.e all pre_run executed)
        for _collector in self.conf["collectors"]:
            while not _collector.ready:
                time.sleep(0.1)

        # Loop until stop was resquested
        while self.running:
            # Notfy Collector threads to get power
            self.notity_collectors()

            # Wait for polling interval
            self._interruptible_sleep(self.conf["polling_interval"])

        self.logger.debug("Stoping collectors for poller")
        # Request stop for all collector threads
        for _collector in self.conf["collectors"]:
            _collector.stop()

        # Notify colelctors eventualy stuck on condition
        self.notity_collectors()

        # Wait for collectors to stop
        self.logger.debug("Waiting for collectors to stop")
        for _collector in self.conf["collectors"]:
            _collector.join()
        self.logger.debug("Poller stoped")


def signal_term_handler():
    """Sigterm signal handler."""
    for running_thread in POLLERS:
        msg = "Stopping thread for poller"
        logging.info(msg)
        running_thread.stop()
    logging.info("Waiting for pollers to stop....")
    for running_thread in POLLERS:
        running_thread.join()
    logging.info("Program terminated")


def get_collector(server, pod, config):
    """Get proper collector instance."""

    if server["type"] == "ilo":
        ilo_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"]
        }
        the_collector = ILOCollector(
            pod["environment"],
            server["id"],
            ilo_server_conf,
            config["RECORDER_API_SERVER"]
        )
    elif server["type"] == "ilo-gui":
        ilo_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"]
        }
        the_collector = ILOGUICollector(
            pod["environment"],
            server["id"],
            ilo_server_conf,
            config["RECORDER_API_SERVER"]
        )

    elif server["type"] == "idrac8-gui":
        idrac_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"]
        }
        the_collector = IDRAC8GUICollector(
            pod["environment"],
            server["id"],
            idrac_server_conf,
            config["RECORDER_API_SERVER"]
        )

    elif server["type"] == "intel-gui":
        intel_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"]
        }
        the_collector = INTELGUICollector(
            pod["environment"],
            server["id"],
            intel_server_conf,
            config["RECORDER_API_SERVER"]
        )

    elif server["type"] == "ibmc-gui":
        ibmc_server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"]
        }
        the_collector = IBMCGUICollector(
            pod["environment"],
            server["id"],
            ibmc_server_conf,
            config["RECORDER_API_SERVER"]
        )

    elif server["type"] == "redfish":
        server_conf = {
            "base_url": "https://{}".format(server["host"]),
            "user": server["user"],
            "pass": server["pass"]
        }
        the_collector = RedfishCollector(
            pod["environment"],
            server["id"],
            server_conf,
            config["RECORDER_API_SERVER"])
    elif server["type"] == "ipmi":
        ipmi_server_conf = {
            "host": server["host"],
            "user": server["user"],
            "pass": server["pass"]
        }

        the_collector = IPMICollector(
            pod["environment"],
            server["id"],
            ipmi_server_conf,
            config["RECORDER_API_SERVER"]
        )
    else:
        msg = "Unsupported power collect method: {}"
        msg += msg.format(server["type"])
        raise Exception(msg)

    the_collector.name = server["type"] + "/" + server["id"]
    return the_collector


def start_pollers():
    """Load conf, parse it, create pollers and collectors and start them."""

    # Load yaml conf file
    with open("conf/collector-settings.yaml", 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError:
            logging.exception("Error while loading config")
            sys.exit()

    # Parse confir to create poller and collectors
    for a_pod in config["PODS"]:
        logging.info(
            "Loading configuration for pod %s",
            a_pod["environment"]
        )

        # Backward compatibility (defaut polling interval)
        if "polling_interval" not in a_pod:
            polling_interval = 10
            logging.warn(
                "\n\n*******************************\n\n"
                "\"polling_interval\" is not set in PODS definition yaml file "
                "(at environment level) using default setting: %ds "
                "\n\n*******************************\n\n",
                polling_interval
            )
        else:
            polling_interval = a_pod["polling_interval"]

        # Current poller config data structure
        poller_conf = {
            "polling_interval": polling_interval,
            "collectors": [],
            "active": True
        }

        if "active" in a_pod:
            poller_conf["active"] = a_pod["active"]

        if poller_conf["active"]:
            # Create collectors for servers and add it to current poller
            for srv in a_pod["servers"]:
                if "active" not in srv or srv["active"]:
                    collector = get_collector(
                        srv,
                        a_pod,
                        config
                    )
                    poller_conf["collectors"].append(collector)
                else:
                    logging.info(
                        "Server %s is not active: skipping",
                        srv["id"]
                    )

            poller = Poller(poller_conf)
            POLLERS.append(poller)

            logging.info(
                "Starting poller threads for pod %s",
                a_pod["environment"]
            )
            poller.start()
        else:
            logging.info(
                "Environment %s is not active: skipping",
                a_pod["environment"]
            )


def main():
    """Execute main code."""

    # Activate signal handler for SIGTERM
    signal.signal(signal.SIGTERM, signal_term_handler)

    # Configure logging
    logging.config.fileConfig("conf/collector-logging.conf")

    logging.info("Server power consumption daemon is starting")

    start_pollers()
    try:
        # Wait until killed
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_term_handler()
    except SystemExit:
        pass
    except Exception:  # pylint: disable=locally-disabled,broad-except
        logging.error(
            "Unexpected error: %s",
            traceback.format_exc()
        )
        signal_term_handler()


if __name__ == "__main__":
    main()
