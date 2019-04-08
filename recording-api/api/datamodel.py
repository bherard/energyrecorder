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
from flask_restplus import fields
from api.restplus import API

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

API_STATUS = API.model('NRGAPIStatus', {
    'status': fields.String(required=True,
                            decription='Current API status')
})

RUNNING_SCENARIO = API.inherit('NRGRunningScenario', RECORDER_POST, {
    'environment': fields.String(required=True,
                                 description='Recorder identifier'),
})

POWER_MEASUREMENT = API.inherit('NRGPowerMeasurement', RUNNING_SCENARIO, {
    'power': fields.Integer(required=True,
                            description='Power consumption in Watts'),
})


# Model description for returned objects
# pylint: disable=locally-disabled,too-few-public-methods
class NRGRunningScenarioClass(object):
    """RunningScenario public object."""

    def __init__(self, environment, scenario, step):
        """
        Constructor: create an instance of NRGRunningScenarioClass.

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
class NRGPowerMeasurementClass(NRGRunningScenarioClass):
    """PowerMeasurement public object."""

    def __init__(self, environment, power, scenario, step):
        """
        Constructor: create an instance of NRGRunningScenarioClass.

            :param environment: Environment on witch power is collected
            :type environment: string

            :param power: Collected power value
            :type power: int

            :param scenario: Scenario during witch power is collected
            :type scenario: string

            :param step: Step of Scenario during witch power is collected
            :type step: string


        """
        NRGRunningScenarioClass.__init__(self, environment, scenario, step)
        self.power = power


# pylint: disable=locally-disabled,too-few-public-methods
class NRGAPIStatusClass(object):
    """API Monitoring status."""

    def __init__(self, status):
        """
        Constructor: create an instance of NRGAPIStatusClass.

            :param status: Current API status
            :type status: string
        """
        self.status = status
