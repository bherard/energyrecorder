# -*- coding: UTF-8 -*-
"""Chassis Management."""
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
import logging

from flask_restplus import Resource
import subprocess
import threading
from api.restplus import API as api
import settings


NS = api.namespace('Chassis',
                   description='Chassis managment')


class YokoThread(threading.Thread):
    def __init__(self, pm, yokopath):
        self._pm = pm
        self._yokopath = yokopath
        self.power = 0
        threading.Thread.__init__(self)
 
    def _get_power_from_yoko(self, dev, pmtype, yokopath):
        """Get power from yoko."""

        sys_cmd = (
            "sudo " +
            yokopath +
            "/yokotool " +
            dev +
            " --pmtype=" + pmtype +
            " read P --count=1"
        )
        data = subprocess.check_output(
            sys_cmd,
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        power = data.split("\n")[1]
        return power

    def run(self):
        self.power = self._get_power_from_yoko(
            self._pm["dev"],
            self._pm["pmtype"],
            self._yokopath
        )
 

@NS.route('/')
class ChassisList(Resource):
    """Chassis class."""

    logger = logging.getLogger(__name__)

    def get(self):
        """Return List of chassis."""
        rc = {
            "Members": [
                {
                    "@odata.id": settings.API["context_root"] + "/Chassis/1/"
                }
            ]
        }
        self.logger.debug(rc)
        return rc


@NS.route('/<string:chassis>')
@NS.route('/<string:chassis>/')
class ChassisDef(Resource):
    """Chassis def class."""
    def get(self, chassis):  # pylint: disable=locally-disabled,no-self-use
        """Return pseud chassis def."""
        ret = {
            "Power": {
                 "@odata.id": "/redfish/v1/Chassis/" + chassis + "/Power/"
            }
        }
        return ret


@NS.route('/1/Power')
@NS.route('/1/Power/')
class ChassisPower(Resource):
    """Chassis Power class."""

    logger = logging.getLogger(__name__)

    def get(self):
        """Return chassis power."""

        power = 0
        pms = []
        for pm in settings.POWERMETERS:
            pm = YokoThread(pm, settings.YOKOTOOL_PATH)
            pm.start()
            pms.append(pm)
        
        for pm in pms:
            pm.join()
            power = power + float(pm.power)

        power = int(round(power))
        rc = {
            "PowerControl": [
                {
                    "PowerConsumedWatts": power,
                }
            ]
        }
        return rc
