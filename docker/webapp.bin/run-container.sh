#!/bin/bash
if [ $# -ne 4 ] ; then
  echo "Usage: "`basename $0`" admin-influx-user-name password redonly-influx-user-name password"
  exit 1
fi
docker run -d  --name energyrecorder-api -p 8086:8086 -p 8888:8888 -v /home/jmjb0521/OPEN-NFV/energyrecorder/web.py/conf:/usr/local/energyrecorder/web.py/conf -v /var/log/energyrecorder/:/var/log/energyrecorder energyrecorder/webapp $*
docker run -d --name influx-chronograf -p 8083:8888 chronograf:alpine
