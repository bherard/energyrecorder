# -*- coding: utf-8 -*-
"""Businness exceptions."""
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
#     Businness exceptions.

class RecordingException(Exception):
    """Scroring Exception."""

    message = None

    def __init__(self, message, http_status):
        """Initliaze exception."""
        Exception.__init__(self, message)
        self.http_status = http_status
        self.message = message

