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
# File Name   : api/endpoints/monitoring.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     API monitoring
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-05-11 : Release of the file
#

import logging

from flask_restx import Resource
from api.datamodel import API_STATUS
from api.restx import API as api
from service.monitoring import MonitoringService


NS = api.namespace(
    'monitoring',
    description='API monitoring'
)


@NS.route('/ping')
class Ping(Resource):
    """API monitoring Ping class."""

    logger = logging.getLogger(__name__)

    @api.marshal_with(API_STATUS)
    def get(self):
        """Return API status."""
        self.logger.debug("GET ping")

        return MonitoringService().connect_influx()
