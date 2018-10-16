#!/bin/bash
function startUwsgi(){
        cat <<EOF > /etc/uwsgi/conf.d/yoko2redfish.ini
[uwsgi]
plugins = python
chdir = /usr/local/yoko2redfish
module = app
callable = APP
socket = /tmp/yoko2redfish.socket
chmod-socket = 777

vacuum = true
die-on-term = true


EOF
        chown uwsgi:uwsgi /etc/uwsgi/conf.d/yoko2redfish.ini
        uwsgi --ini /etc/uwsgi/uwsgi.ini >> /var/log/uwsgi/uwsgi.log 2>&1 &
        sleep 1

}


function startNginx(){
        cat <<EOF > /etc/nginx/conf.d/default.conf
server {
        listen 80 default_server;
        listen [::]:80 default_server;

        location / {
                include uwsgi_params;
                uwsgi_pass unix:/tmp/yoko2redfish.socket;
        }

}
EOF
        mkdir -p /run/nginx
        nginx -g "daemon off;" >/dev/null
}


function confApp(){
        mkdir -p /var/log/yoko2redfish
        chmod a+w /var/log/yoko2redfish
        sed -i 's|^YOKOTOOL_PATH.*|YOKOTOOL_PATH: /usr/local/yoko-tool|' /usr/local/yoko2redfish/conf/webapp-settings.yaml;
}

function confSudo(){
        cat<<EOF >/etc/sudoers.d/yokotool
Cmnd_Alias      YOKOTOOL=/usr/local/yoko-tool/yokotool
User_Alias      YOKO_USERS=uwsgi  YOKO_USERS       ALL = NOPASSWD: YOKOTOOL
EOF
}

confApp
confSudo
startUwsgi
startNginx


