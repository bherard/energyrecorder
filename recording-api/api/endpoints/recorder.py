# -*- coding: utf-8 -*-
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

from flask_restx import Resource
from flask import request
import settings
from api.datamodel import RUNNING_SCENARIO
from api.datamodel import STEP_POST, RECORDER_POST
from api.restx import API as api
from service.datamodel import RunningScenarioClass
from service.exception import RecordingException
from service.recorder import RecorderService

NS = api.namespace('recorders',
                   description='Recording sessions management')

PARSER = api.parser()
PARSER.add_argument('time', type=int,
    help='POSIX Timestamp (in nanosec) recorder started immediatly \
            before this time',
    default=None,
    location='args'
)


@NS.route('/environment/<string:env>')
@api.doc(params={'env': 'Environment identifier'})
class Recorder(Resource):
    """Recorder services management class."""

    logger = logging.getLogger(__name__)


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
        self.logger.info(
            "GET env=%s",
            env
        )

        args = PARSER.parse_args(request)
        time = args.get('time', None)

        svc = RecorderService()
        try:
            result = svc.load_session(env, time)
            self.logger.debug(result)
        except RecordingException as exc:
            api.abort(exc.http_status, exc.message)
        return result

    @api.marshal_with(RUNNING_SCENARIO)
    def delete(self, env):
        """
        Stop a session.

        Stop a data recording session
            :param env: Environement identifier
            :type env: string
        """
        self.logger.info(
            "DELETE env=%s",
            env
        )

        svc = RecorderService()

        try:

            result = svc.load_session(env)
            svc.store_session(env, result.scenario, result.step, 0)
        except RecordingException as exc:
            api.abort(exc.http_status, exc.message)

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
        self.logger.info(
            "POST env=%s scenario=%s step=%s",
            env,
            data.get("scenario"),
            data.get("step")
        )

        svc = RecorderService()
        try:
            result =  svc.store_session(env, data.get("scenario"), data.get("step"))
        except RecordingException as exc:
            api.abort(exc.http_status, exc.message)

        return result

@NS.route('/environment/<string:env>/step')
class RecorderStep(Resource):
    """Recorder steps services management class."""

    logger = logging.getLogger(__name__)

    @api.marshal_with(RUNNING_SCENARIO)
    @api.expect(STEP_POST)
    def post(self, env):    # pylint: disable=no-self-use
        """
        Define current step.

        Define current step for a recording scenartion
            :param env: Environement identifier
            :type env: string
        """
        recorder = RecorderService()
        data = request.json

        self.logger.info(
            "POST step env=%s step=%s",
            env,
            data.get("step")
        )

        try:

            result = recorder.load_session(env)

            result.step = data.get("step")
            recorder.store_session(env, result.scenario, result.step)
        except RecordingException as exc:
            api.abort(exc.http_status, exc.message)

        return result
