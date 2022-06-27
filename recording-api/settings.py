# -*- coding: utf-8 -*-
"""Record API configuration parameters."""
# --------------------------------------------------------
# Module Name : terraHouat power recording API
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
# File Name   : terrhouat/settings.py
#
# Created     : 2017-02
# Authors     : Benoit HERARD <benoit.herard(at)orange.com>
#
# Description :
#     API Settings
# -------------------------------------------------------
# History     :
# 1.0.0 - 2017-02-20 : Release of the file
# Flask settings
FLASK_DEBUG = False  # Do not use debug mode in production

# Flask-Restplus settings
RESTX_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTX_VALIDATE = True
RESTX_MASK_SWAGGER = False
RESTX_ERROR_404_HELP = False

API = {
    "context_root": "/resources",
    "version": '1.0',
    "title": 'Energy monitoring API',
    "description": 'PODs Energy consumption gathering API'
}

INFLUX = {}
BIND = None
MQTT = {}

ALWAYS_RECORD = True
