FROM alpine
MAINTAINER benoit.herard@orange.com

RUN apk update;\
    apk add git bash python py-pip ipmitool; \
    pip install --upgrade pip; \
    pip install virtualenv; \
    cd /usr/local;\
    git clone https://github.com/bherard/energyrecorder;\
    cd energyrecorder;\
    virtualenv venv;\
    source venv/bin/activate;\
    pip install -r server-collector/requirements.txt


ENTRYPOINT /usr/local/energyrecorder/bin/run-collector.sh
