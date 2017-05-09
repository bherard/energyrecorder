FROM ubuntu:16.04
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
    pip install -r server-collector/requirements.txt"

ENTRYPOINT /usr/local/energyrecorder/bin/run-collector.sh
