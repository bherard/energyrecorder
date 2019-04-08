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
"""yoko2redfish configuration parameters."""
# Flask settings
FLASK_DEBUG = False  # Do not use debug mode in production

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False
RESTPLUS_ERROR_404_HELP = False

API = {
    "context_root": "/redfish/v1",
    "version": '1.0',
    "title": 'YOKO Powermeter to redfish',
    "description": 'Minimal implementation to get YOYO Powermeter Power '
                   'as redfish API.'
}

BIND = None
POWERMETERS = []
YOKOTOOL_PATH = ""
