        #!/bin/bash

function startInflux(){
        influxd &
        sleep 20
        if [ "$1" != "" ] ; then
                AUTH_ENABLED=true
                echo "show databases" | influx -username "$1" -password "$2"|grep NRG
        else
                AUTH_ENABLED=false
                echo "show databases" | influx |grep NRG
        fi
        if [ $? -ne 0 ] ; then
                curl https://raw.githubusercontent.com/bherard/energyrecorder/master/influx/creation.iql|influx
                echo "CREATE USER $1 WITH PASSWORD '"$2"' WITH ALL PRIVILEGES;"> /tmp/create.iql
                echo "CREATE USER $3 WITH PASSWORD '"$4"';">> /tmp/create.iql
                echo "GRANT READ ON NRG TO $3;">> /tmp/create.iql
                cat /tmp/create.iql
                cat /tmp/create.iql | influx
                rm /tmp/create.iql
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
        influxd -config  /etc/influxdb/influxdb.conf &

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
        if [ "$1" != "" ] ; then
                cd /usr/local/energyrecorder/recording-api/conf/
                sed -i 's/^.*user:.*/    user: "'$1'"/' webapp-settings.yaml
                sed -i 's/^.*pass:.*/    pass: "'$2'"/' webapp-settings.yaml
        fi
}

function usage(){
        cat <<EOF
container start parameters:  [-admin-user USER] [-admin-password PASS] [-readonly-user USER] [-readonly-password PASS] [-proxy PROXY] [-noinflux] [-h]
        -proxy: When stating, container download some additional config files. If container can't connect internet directly define proxy to use with this flag.
        -nofinflux: Embed InfluxDB server is not configured nor started with API. (if set, you have to manulaly configure API DB Conenction parameters).
        -admin-user USER: Influx DB admin user name (all privileges).
        -admin-password PASS: Password for admin user.
        -readonly-username USER: Influx DB user name with read on privileges.
        -readonly-password PASS: Password for read only user name.
        -h: this message.

NOTE:
        * -admin-user, -admin-password, -readonlyuser and -readonly-password should be set all together or none of them.
        * -admin-user, -admin-password, -readonlyuser and -readonly-password make no sens with -noinflux.
VOLUME MOUNT (useful path in the container to bind as  volume):
        * influxDB configuration is located in /etc/influxdb/influxdb.conf
        * influxDB data is located in /var/lib/influxdb/
        * API config files (incl. logging) is located in /usr/local/energyrecorder/recording-api/conf/
        * API logs are located in /var/log/energyrecorder


LISTENING PORT:
        * API is listening on port 80 (Swagger for API available at http://container/resources/doc/ )
        * Influx is listening on port 8086
EOF
        exit 0
}


ADMIN_USER=""
ADMIN_PASS=""
READER_USER=""
READER_PASS=""
INFLUX=1
while [ "$1" != "" ] ; do
        if [ "$1" == "-admin-user" ] ; then
                shift
                ADMIN_USER="$1" 
        elif [ "$1" == "-admin-password" ] ; then
                shift
                ADMIN_PASS="$1"
        elif [ "$1" == "-readonly-user" ] ; then
                shift
                READER_USER="$1" 
        elif [ "$1" == "-readonly-password" ] ; then
                shift
                READER_PASS="$1"
        elif [ "$1" == "-proxy" ] ; then
                shift 
                export http_proxy="$1"
                export https_proxy="$1"
                echo "proxy set to $1"
        elif [ "$1" == "-noinflux" ] ; then
                INFLUX=0
        elif [ "$1" == "-h" ] ; then
                usage
        fi
        shift
done

if [ "$ADMIN_USER" != "" -o "$ADMIN_PASS" != "" -o "$READER_USER" != "" -o "$READER_PASS" != "" ] ; then
        if [ "$ADMIN_USER" == "" -o "$ADMIN_PASS" == "" -o "$READER_USER" == "" -o "$READER_PASS" == "" ] ; then
                echo "-admin-user, -admin-password, -readonlyuser and -readonly-password should be set all together or none of them."
                exit 1
        fi
fi

confApp "$1" "$2"
if [ $INFLUX -eq 1 ] ; then
        startInflux "$1" "$2" "$3" "$4"
fi
startUwsgi
startNginx
while [ 1 ] ; do
        sleep 1
done

