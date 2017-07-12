#!/bin/bash
nohup python /usr/local/energyrecorder/recording-api/app.py &
influxd &
sleep 1
echo "show databases" | influx -username "$1" -password "$2"|grep NRG
if [ $? -ne 0 ] ; then
        curl https://raw.githubusercontent.com/bherard/energyrecorder/master/influx/creation.iql|influx
        echo "CREATE USER $1 WITH PASSWORD '"$2"' WITH ALL PRIVILEGES"|influx
        echo "CREATE USER $3 WITH PASSWORD '"$4"'"|influx
        echo "GRANT READ ON NRG TO energyreader"|influx
else
        echo "Database already exists"
fi
if [ ! -f /etc/ssl/influxdb.pem ] ; then
        /usr/local/bin/create-certs.sh
fi
grep '\[http\]' /etc/influxdb/influxdb.conf >/dev/null
if [ $? -ne 0 ] ; then
        cat <<EOF >> /etc/influxdb/influxdb.conf

[http]
  enabled = true
  auth-enabled = false
  https-enabled = false
  https-certificate = "/etc/ssl/influxdb.pem"
EOF
fi
ps ax|grep influxd|grep -v grep|awk '{print $1}'|xargs kill -9
influxd
