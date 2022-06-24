# -*- coding: utf-8 -*-
"""Restplus library configuration and startup."""
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
# File Name   : api/restx.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     Restplus configuration
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
#
import logging

from flask_restx import Api
import settings

LOG = logging.getLogger(__name__)

# Settings for swagger meta API
API = Api(version=settings.API["version"],
          title=settings.API["title"],
          description=settings.API["description"],
          doc="/doc/")


@API.errorhandler
def default_error_handler(root_exception):
    """Return encountred error in REST compliant way."""
    message = 'An unhandled exception occurred.' + str(root_exception)
    LOG.exception(message)

    if not settings.FLASK_DEBUG:
        return {'message': message}, 500
