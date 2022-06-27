# -*- coding: utf-8 -*-
"""Scenarios and scenarios steps management."""
# --------------------------------------------------------
# Module Name : power recording API
# Version : 1.0
#
# Copyright © 2022 Orange
# This software is distributed under the Apache 2 license
# <http://www.apache.org/licenses/LICENSE-2.0.html>
#
# -------------------------------------------------------
# Created     : 2022-06
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Scenarios and scenarios steps management.

import logging
import json
import urllib
import requests

import settings
from service.datamodel import RunningScenarioClass
from service.exception import RecordingException

RUNNING_SCENARIO_RP = "running_scenarios_rp"


class RecorderService:
    """Recorder services management class."""

    logger = logging.getLogger(__name__)

    # pylint: disable=no-self-use
    def load_session(self, env, time=None):
        """
        Load current recording session description.

            :param env: Environnement identifier
            :type env: string

            :param time: For witch timestamp recorder is searched
            :type time: int POSIX timestamp in ns

        """
        if time is None:
            str_select = "SELECT last(started), * \
                          FROM " + RUNNING_SCENARIO_RP + ".RunningScenarios \
                          WHERE environment='" + env + "'"
        else:
            str_select = "SELECT last(started), * \
                          FROM " + RUNNING_SCENARIO_RP + ".RunningScenarios \
                          WHERE environment='" + env + "' \
                          AND time <=" + str(time)

        if settings.INFLUX["user"] is not None:
            auth = (settings.INFLUX["user"], settings.INFLUX["pass"])
        else:
            auth = None

        influx_url = settings.INFLUX["host"] + "/query?q="
        influx_url += urllib.parse.quote(str_select)
        influx_url += "&db=" + urllib.parse.quote(settings.INFLUX["db"])
        response = requests.get(influx_url, auth=auth, verify=False)
        if response.status_code == 200:
            json_object = json.loads(response.text)

            if "series" in json_object["results"][0]:
                scenario = json_object["results"][0]["series"][0]["values"][0][3]
                step = json_object["results"][0]["series"][0]["values"][0][5]
                started = json_object["results"][0]["series"][0]["values"][0][4
                ]
                if started == 1:
                    result = RunningScenarioClass(env, scenario, step)
                    return result
                else:
                    err_text = "Can't find any recording session "
                    err_text += F"for recorder \"{env}\""
                    
                    raise RecordingException(err_text, 404)
            else:
                err_text = "Can't find any recording session "
                err_text += F"for recorder \"{env}\""
                    
                raise RecordingException(err_text, 404)
        else:
            err_text = "Can't find any recording session "
            err_text += F"for recorder \"{env}\""

            log_msg = "Error while contacting influxDB HTTP Code={} Body={}"
            log_msg = log_msg.format(response.status_code, response.text)
            self.logger.error(
                "Error while contacting influxDB HTTP Code=%d Body=%s",
                response.status_code,
                response.text
            )
            raise RecordingException(err_text, response.status_code)

    # pylint: disable=no-self-use
    def store_session(self, env, scenario, step, started=1):
        """
        Store a new recording session in influxDB.

            :param env: Environment on witch power is collected
            :type env: string

            :param scenario: Scenario during witch power is collected
            :type scenario: string

            :param step: Step of Scenario during witch power is collected
            :type step: string

        """
        result = RunningScenarioClass(env, scenario, step)

        influx_data = "RunningScenarios,environment="
        influx_data += result.environment.replace(' ', '\\ ')
        influx_data += ",scenario="
        influx_data += result.scenario.replace(' ', '\\ ')
        influx_data += ",step="
        influx_data += result.step.replace(' ', '\\ ')
        influx_data += " started=" + str(started)

        self.logger.debug(settings.INFLUX["host"] +
                          "/write?db=" + settings.INFLUX["db"])
        self.logger.debug(influx_data)

        if settings.INFLUX["user"] is not None:
            auth = (settings.INFLUX["user"], settings.INFLUX["pass"])
        else:
            auth = None

        influx_url = settings.INFLUX["host"]
        influx_url += "/write?db="
        influx_url += settings.INFLUX["db"]
        influx_url += "&rp=" + RUNNING_SCENARIO_RP
        response = requests.post(
            influx_url,
            data=influx_data,
            auth=auth,
            verify=False)
        if response.status_code != 204:
            log_msg = F"Error while storing recorder: {response.text}"
            
            raise RecordingException(log_msg, 500)

        return result
