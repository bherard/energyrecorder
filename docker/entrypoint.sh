#!/bin/bash
nohup /usr/local/energyrecorder/bin/run-webapp.sh &
influxd &
sleep 1
curl https://raw.githubusercontent.com/bherard/energyrecorder/master/web.py/creation.iql|influx -ssl -unsafeSsl
ps aux|grep influxd|grep -v grep|awk '{print $2}'|xargs kill -9
/usr/local/bin/create-certs.sh
cat <<EOF >>i /etc/influxdb/influxdb.conf 

[http]
  enabled = true
  auth-enabled = false
  https-enabled = true
	https-certificate = "/etc/ssl/influxdb.pem"

[admin]
	enabled = true
	https-enabled = true
	https-certificate = "/etc/ssl/influxdb.pem"
EOF
influxd 

