FROM influxdb
MAINTAINER benoit.herard@orange.com

RUN bash -c "apt-get update;\
    apt-get install -y git python python-pip; \
    pip install --upgrade pip; \
    pip install virtualenv; \
    cd /usr/local;\
    git clone https://github.com/bherard/energyrecorder;\
    cd energyrecorder;\
    virtualenv venv;\
    source venv/bin/activate;\
    pip install -r web.py/requirements.txt;\
    mv /entrypoint.sh /influx-entrypoint.sh;\
    echo '#!/bin/bash' > /entrypoint.sh;\
    echo 'nohup /usr/local/energyrecorder/bin/run-webapp.sh &' >> /entrypoint.sh;\
    echo 'influxd' >> /entrypoint.sh;\
    echo 'curl https://raw.githubusercontent.com/bherard/energyrecorder/master/web.py/creation.iql|influx' >> /entrypoint.sh;\
    chmod u+x /entrypoint.sh;"

#RUN bash -c "nohup influxd &" ; sleep 1 ; influx < /usr/local/energyrecorder/web.py/creation.iql


ENTRYPOINT /entrypoint.sh
