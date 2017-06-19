#!/bin/bash
nohup /usr/local/energyrecorder/bin/run-webapp.sh &
influxd &
sleep 1
curl https://raw.githubusercontent.com/bherard/energyrecorder/master/web.py/creation.iql|influx
echo "CREATE USER energymaster WITH PASSWORD '"$1"' WITH ALL PRIVILEGES"|influx
echo "CREATE USER energyreader WITH PASSWORD '"$2"'"|influx
echo "GRANT READ ON NRG TO energyreader"|influx

ps aux|grep influxd|grep -v grep|awk '{print $2}'|xargs kill -9
/usr/local/bin/create-certs.sh
cat <<EOF >> /etc/influxdb/influxdb.conf 

[http]
  enabled = true
  auth-enabled = true
  https-enabled = true
	https-certificate = "/etc/ssl/influxdb.pem"

[admin]
	enabled = true
	https-enabled = true
	https-certificate = "/etc/ssl/influxdb.pem"
EOF
influxd 

