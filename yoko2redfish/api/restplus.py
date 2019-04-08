# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Module Name : power recording API
#               request YOKOGAWA Powermeter with redfish
# Version : 1.0
#
# Copyright © 2018 Orange
# This software is distributed under the Apache 2 license
# <http://www.apache.org/licenses/LICENSE-2.0.html>
#
# -------------------------------------------------------
#
# Created     : 2018-10
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     API monitoring
# -------------------------------------------------------
# History     :
# 1.0.0 - 2018-10-16 : Release of the file
#
"""Restplus library configuration and startup."""
import logging

from flask_restplus import Api
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
