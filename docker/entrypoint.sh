#!/bin/bash
nohup /usr/local/energyrecorder/bin/run-webapp.sh &
influxd &
sleep 1
curl https://raw.githubusercontent.com/bherard/energyrecorder/master/web.py/creation.iql|influx
echo "CREATE USER $1 WITH PASSWORD '"$2"' WITH ALL PRIVILEGES"|influx
echo "CREATE USER $3 WITH PASSWORD '"$4"'"|influx
echo "GRANT READ ON NRG TO energyreader"|influx

ps aux|grep influxd|grep -v grep|awk '{print $2}'|xargs kill -9
/usr/local/bin/create-certs.sh
cat <<EOF >> /etc/influxdb/influxdb.conf

[http]
  enabled = true
  auth-enabled = False
  https-enabled = False
	https-certificate = "/etc/ssl/influxdb.pem"

[admin]
	enabled = true
	https-enabled = False
	https-certificate = "/etc/ssl/influxdb.pem"
EOF
influxd
