# -*- coding: utf-8 -*-
"""Businness data model."""
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
#     Businness data model.

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
