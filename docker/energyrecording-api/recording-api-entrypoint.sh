        #!/bin/bash
# cd /usr/local/energyrecorder/recording-api/
# export PYTHONPATH=.:$PYTHONPATH
# python app.py &

function startInflux(){
        influxd &
        sleep 20
        if [ "$1" != "" ] ; then
                echo "show databases" | influx -username "$1" -password "$2"|grep NRG
        else
                echo "show databases" | influx |grep NRG
        fi
        if [ $? -ne 0 ] ; then
                curl https://raw.githubusercontent.com/bherard/energyrecorder/master/influx/creation.iql|influx
                echo "CREATE USER $1 WITH PASSWORD '"$2"' WITH ALL PRIVILEGES"|influx
                echo "CREATE USER $3 WITH PASSWORD '"$4"'"|influx
                echo "GRANT READ ON NRG TO $3"|influx
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
auth-enabled = $AUTH_ENABLED
https-enabled = false
https-certificate = "/etc/ssl/influxdb.pem"
flux-enabled = true
EOF
        fi
        ps ax|grep influxd|grep -v grep|awk '{print $1}'|xargs kill -9
        influxd &

}

function startUwsgi(){
        unset http_proxy
        unset https_proxy
        cat <<EOF > /etc/uwsgi/conf.d/energyrecorder.ini
[uwsgi]
plugins = python3
chdir = /usr/local/energyrecorder/recording-api
module = app
callable = APP
socket = /tmp/recorder.socket
chmod-socket = 777
processes = $(expr $(nproc) + 1)
enable-threads = True


vacuum = true
die-on-term = true


EOF
        chown uwsgi:uwsgi /etc/uwsgi/conf.d/energyrecorder.ini
        uwsgi --ini /etc/uwsgi/uwsgi.ini &
        sleep 1

}


function startNginx(){
        unset http_proxy
        unset https_proxy
        sed -i 's/^\(.*client_max_body_size\).*/\1 20m;/' /etc/nginx/nginx.conf
        cat <<EOF > /etc/nginx/conf.d/default.conf
server {
        listen 80 default_server;
        listen [::]:80 default_server;

        location / {
                include uwsgi_params;
                uwsgi_pass unix:/tmp/recorder.socket;
        }

}
server {
        listen 8888 ;
        listen [::]:8888 ;

        location / {
                include uwsgi_params;
                uwsgi_pass unix:/tmp/recorder.socket;
        }

}
EOF
        mkdir -p /run/nginx
        nginx -g "daemon off;"
}


function confApp(){
        if [ ! -f /usr/local/energyrecorder/recording-api/conf/webapp-logging.conf ] ; then
                cp /usr/local/energyrecorder/recording-api/conf/webapp-logging.conf.sample /usr/local/energyrecorder/recording-api/conf/webapp-logging.conf
                mkdir -p /var/log/energyrecorder
                chmod a+w /var/log/energyrecorder
        fi
        if [ ! -f /usr/local/energyrecorder/recording-api/conf/webapp-settings.yaml ] ; then
                cp /usr/local/energyrecorder/recording-api/conf/webapp-settings.yaml.sample /usr/local/energyrecorder/recording-api/conf/webapp-settings.yaml
        fi
}
if [ "$5" == "proxy" -a "$6" != "" ] ; then
        export http_proxy=$6
        export https_proxy=$6
        echo "proxy set to $6"
fi

echo "ARGS=$*"
confApp
startInflux "$1" "$2" "$3" "$4"
startUwsgi
startNginx


