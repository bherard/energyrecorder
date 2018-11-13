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
import subprocess
import threading
from flask_restplus import Resource
from api.restplus import API as api
import settings


NS = api.namespace('Chassis',
                   description='Chassis managment')


class YokoThread(threading.Thread):
    """Intercat with YOKO Powermeter with yototool."""
    def __init__(self, pm, yokopath):
        self._pm = pm
        self._yokopath = yokopath
        self.power = 0
        self.logger = logging.getLogger(self.__class__.__name__)
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
        self.logger.debug("Getting power for YOKO: %s", sys_cmd)
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

    # pylint: disable=redefined-outer-name,keyword-arg-before-vararg
    def __init__(self, api=None, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        Resource.__init__(self, api, args, kwargs)

    def get(self):
        """Return List of chassis."""

        self.logger.debug("GET /Chassis")
        ret = {
            "Members": [
                {
                    "@odata.id": settings.API["context_root"] + "/Chassis/1/"
                }
            ]
        }
        self.logger.debug(ret)
        return ret


@NS.route('/<string:chassis>')
@NS.route('/<string:chassis>/')
class ChassisDef(Resource):
    """Chassis def class."""

    # pylint: disable=redefined-outer-name,keyword-arg-before-vararg
    def __init__(self, api=None, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        Resource.__init__(self, api, args, kwargs)

    def get(self, chassis):  # pylint: disable=locally-disabled,no-self-use
        """Return pseud chassis def."""

        self.logger.debug("GET /Chassis/%s", chassis)
        ret = {
            "Power": {
                "@odata.id": "/redfish/v1/Chassis/" + chassis + "/Power/"
            }
        }
        return ret


@NS.route('/<string:chassis>/Power')
@NS.route('/<string:chassis>/Power/')
class ChassisPower(Resource):
    """Chassis Power class."""

    # pylint: disable=redefined-outer-name,keyword-arg-before-vararg
    def __init__(self, api=None, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        Resource.__init__(self, api, args, kwargs)

    def get(self, chassis):
        """Return chassis power."""

        self.logger.debug("GET /Chassis/%s/Power", chassis)
        power = 0
        pms = []
        for _pmeter in settings.POWERMETERS:
            pmeter = YokoThread(_pmeter, settings.YOKOTOOL_PATH)
            pmeter.start()
            pms.append(pmeter)

        for _pmeter in pms:
            _pmeter.join()
            power = power + float(_pmeter.power)

        power = int(round(power))
        ret = {
            "PowerControl": [
                {
                    "PowerConsumedWatts": power,
                }
            ]
        }
        return ret
