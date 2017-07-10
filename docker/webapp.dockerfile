FROM influxdb:alpine
MAINTAINER benoit.herard@orange.com

RUN apk update;\
    apk add git python py-pip bash ca-certificates ; \
    update-ca-certificates ; \
    apk add openssl
    pip install --upgrade pip; \
    pip install virtualenv; \
    cd /usr/local;\
    git clone https://github.com/bherard/energyrecorder;\
    cd energyrecorder;\
    virtualenv venv;\
    . venv/bin/activate;\
    pip install -r web.py/requirements.txt;\
    mv /entrypoint.sh /influx-entrypoint.sh;

RUN wget https://raw.githubusercontent.com/bherard/energyrecorder/master/docker/entrypoint.sh -O /entrypoint.sh;\
	chmod u+x /entrypoint.sh;\
	wget https://raw.githubusercontent.com/bherard/energyrecorder/master/influx/create-certs.sh -O /usr/local/bin/create-certs.sh;\
	chmod u+x /usr/local/bin/create-certs.sh;\
	echo DONE

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
#apk update && apk add ca-certificates && update-ca-certificates && apk add openssl
