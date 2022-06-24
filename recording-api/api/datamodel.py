# -*- coding: utf-8 -*-
"""Recorder API publich datamodel descriptions."""
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
# File Name   : api/datamodel.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Public data model definitions
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
#
from flask_restx import fields
from api.restx import API

# Model desecription for methods parameters
POWER_POST = API.model('powerPost', {
    'power': fields.Integer(required=True,
                            description='Power consumption in Watts'),
    'time': fields.Integer(required=False,
                           description='Measurment time stamp'),
    'environment': fields.String(required=True,
                                 description='Recorder environment \
                                              identifier'),
})
MEASUREMENT = API.model("measurement", {
    'sensor': fields.String(
        required=True,
        description="Sensor/measurment name"
    ),
    'unit': fields.String(
        required=True,
        description='Measurement unit'
    ),
    'value': fields.Float(
        required=True,
        decription='Measurement value'
    ),
    'time': fields.Integer(
        required=False,
        description="Measurement timestamp (default= current_timestamp)"
    )
})
MEASUREMENT_POST = API.model("measurementPost", {
    'environment': fields.String(
        required=True,
        description='Recorder environment identifier'
    ),
    "measurements": fields.List(
        fields.Nested(MEASUREMENT),
        required=True,
        description="List of measurements to store"
    )

})
STEP_POST = API.model('stepPost', {
    'step': fields.String(required=True,
                          description='New step for current \
                                       recording scenario')
})
RECORDER_POST = API.model('recorderPost', {
    'scenario': fields.String(required=True,
                              description='Current recording scenario'),
    'step': fields.String(required=True,
                          description='Current step of this scenario'),
})

API_STATUS = API.model('APIStatus', {
    'status': fields.String(required=True,
                            decription='Current API status')
})

RUNNING_SCENARIO = API.inherit('runningScenario', RECORDER_POST, {
    'environment': fields.String(required=True,
                                 description='Recorder identifier'),
})

POWER_MEASUREMENT = API.inherit('powerMeasurement', RUNNING_SCENARIO, {
    'power': fields.Integer(required=True,
                            description='Power consumption in Watts'),
})


# Model description for returned objects
# pylint: disable=locally-disabled,too-few-public-methods
class RunningScenarioClass(object):
    """RunningScenario public object."""

    def __init__(self, environment, scenario, step):
        """
        Constructor: create an instance of RunningScenarioClass.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param scenario: Scenario during witch power is collected
            :type scenario: string

            :param step: Step of Scenario during witch power is collected
            :type step: string


        """
        self.environment = environment
        self.scenario = scenario
        self.step = step


# pylint: disable=locally-disabled,too-few-public-methods
class PowerMeasurementClass(RunningScenarioClass):
    """PowerMeasurement public object."""

    def __init__(self, environment, power, scenario, step):
        """
        Constructor: create an instance of RunningScenarioClass.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param power: Collected power value
            :type power: int

            :param scenario: Scenario during witch power is collected
            :type scenario: string

            :param step: Step of Scenario during witch power is collected
            :type step: string


        """
        RunningScenarioClass.__init__(self, environment, scenario, step)
        self.power = power


# pylint: disable=locally-disabled,too-few-public-methods
class APIStatusClass(object):
    """API Monitoring status."""

    def __init__(self, status):
        """
        Constructor: create an instance of APIStatusClass.

            :param status: Current API status
            :type status: string
        """
        self.status = status
