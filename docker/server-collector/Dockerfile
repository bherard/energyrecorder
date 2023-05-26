FROM python:3.9
LABEL maintainer="benoit.herard@orange.com"

RUN apk update;\
    apk add git bash ipmitool libc-dev gcc; \
    pip3 install --upgrade pip; \
    ln -s /usr/bin/python3 /usr/bin/python; \
    cd /usr/local;\
    git clone https://github.com/bherard/energyrecorder;\
    cd energyrecorder;\
    pip3 install -r server-collector/requirements.txt

ENTRYPOINT cd /usr/local/energyrecorder/server-collector && export PYTHONPATH=.:$PYTHONPATH && python daemon.py
