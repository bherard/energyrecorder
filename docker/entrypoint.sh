#!/bin/bash
nohup /usr/local/energyrecorder/bin/run-webapp.sh &
influxd &
sleep 1
echo "show databases" | influx -username "$1" -password "$2"|grep NRG
if [ $? -ne 0 ] ; then
        curl https://raw.githubusercontent.com/bherard/energyrecorder/master/web.py/creation.iql|influx
        echo "CREATE USER $1 WITH PASSWORD '"$2"' WITH ALL PRIVILEGES"|influx
        echo "CREATE USER $3 WITH PASSWORD '"$4"'"|influx
        echo "GRANT READ ON NRG TO energyreader"|influx
else
        echo "Database already exists"
fi
if [ ! -f /etc/ssl/influxdb.pem ] ; then
        /usr/local/bin/create-certs.sh
fi
grep '\[admin\]' /etc/influxdb/influxdb.conf >/dev/null
if [ $? -ne 0 ] ; then
        cat <<EOF >> /etc/influxdb/influxdb.conf

[http]
enabled = true
auth-enabled = false
https-enabled = false
https-certificate = "/etc/ssl/influxdb.pem"

[admin]
enabled = true
https-enabled = false
https-certificate = "/etc/ssl/influxdb.pem"
EOF
fi
ps aux|grep influxd|grep -v grep|awk '{print $2}'|xargs kill -9
influxd
