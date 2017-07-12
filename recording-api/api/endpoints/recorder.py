# -*- coding: UTF-8 -*-
"""Recorder API Management."""
# --------------------------------------------------------
# Module Name : power recording API
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
# File Name   : api/endpoints/recorder.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Recording sessions management
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
#

import logging
import json
import urllib
import requests

from flask_restplus import Resource
from flask import request
import settings
from api.datamodel import RUNNING_SCENARIO, NRGRunningScenarioClass
from api.datamodel import STEP_POST, RECORDER_POST
from api.restplus import API as api

RUNNING_SCENARIO_RP = "running_scenarios_rp"

NS = api.namespace('recorders',
                   description='Recording sessions management')

PARSER = api.parser()
PARSER.add_argument('time', type=int,
                    help='POSIX Timestamp (in nanosec) recorder started immediatly \
                          before this time',
                    default=None)


@NS.route('/environment/<string:env>')
@api.doc(params={'env': 'Environment identifier'})
class Recorder(Resource):
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

        self.logger.debug(str_select)

        if settings.INFLUX["user"] is not None:
            auth = (settings.INFLUX["user"], settings.INFLUX["pass"])
        else:
            auth = None

        influx_url = settings.INFLUX["host"] + "/query?q="
        influx_url += urllib.quote_plus(str_select)
        influx_url += "&db=" + urllib.quote_plus(settings.INFLUX["db"])
        response = requests.get(influx_url, auth=auth, verify=False)
        if response.status_code == 200:
            json_object = json.loads(response.text)

            if "series" in json_object["results"][0]:
                scenario = json_object[
                    "results"
                ][
                    0
                ][
                    "series"
                ][
                    0
                ][
                    "values"
                ][
                    0
                ][
                    3
                ]
                step = json_object[
                    "results"
                ][
                    0
                ][
                    "series"
                ][
                    0
                ][
                    "values"
                ][
                    0
                ][
                    5
                ]
                started = json_object[
                    "results"
                ][
                    0
                ][
                    "series"
                ][
                    0
                ][
                    "values"
                ][
                    0
                ][
                    4
                ]
                if started == 1:
                    result = NRGRunningScenarioClass(env, scenario, step)
                    return result
                else:
                    err_text = "Can't find any recording session "
                    err_text += "for recorder \"{}\""
                    err_text = err_text.format(env)
                    api.abort(404, err_text)
            else:
                err_text = "Can't find any recording session "
                err_text += "for recorder \"{}\""
                err_text = err_text.format(env)
                api.abort(404, err_text)
        else:
            err_text = "Can't find any recording session "
            err_text += "for recorder \"{}\""
            err_text = err_text.format(env)

            log_msg = "Error while contacting influxDB HTTP Code={} Body={}"
            log_msg = log_msg.format(response.status_code, response.text)
            self.logger.error(log_msg)
            api.abort(500, err_text)

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
        result = NRGRunningScenarioClass(env, scenario, step)

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
            log_msg = "Error while storing recorder: {}"
            log_msg = log_msg.format(response.text)
            api.abort(500, log_msg)

        return result

    @api.marshal_with(RUNNING_SCENARIO)
    @api.response(404, "Can't find any running session.")
    @api.doc(parser=PARSER)
    def get(self, env):
        """
        Get current recording session.

        Get informations about the current recording session
            :param env: Environement identifier
            :type env: string
        """
        args = PARSER.parse_args(request)
        time = args.get('time', None)

        result = self.load_session(env, time)
        self.logger.debug(result)
        return result

    @api.marshal_with(RUNNING_SCENARIO)
    def delete(self, env):
        """
        Stop a session.

        Stop a data recording session
            :param env: Environement identifier
            :type env: string
        """
        result = self.load_session(env)

        self.store_session(env, result.scenario, result.step, 0)

        return result

    @api.marshal_with(RUNNING_SCENARIO)
    @api.expect(RECORDER_POST)
    def post(self, env):
        """
        Start a session.

        Start a data recording session
            :param env: Environement identifier
            :type env: string
        """
        data = request.json
        return self.store_session(env, data.get("scenario"), data.get("step"))


@NS.route('/environment/<string:env>/step')
class RecorderStep(Resource):
    """Recorder steps services management class."""

    @api.marshal_with(RUNNING_SCENARIO)
    @api.expect(STEP_POST)
    def post(self, env):    # pylint: disable=no-self-use
        """
        Define current step.

        Define current step for a recording scenartion
            :param env: Environement identifier
            :type env: string
        """
        recorder = Recorder()
        result = recorder.load_session(env)

        data = request.json
        result.step = data.get("step")
        recorder.store_session(env, result.scenario, result.step)

        return result
