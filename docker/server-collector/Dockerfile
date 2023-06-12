FROM python:3.9
LABEL maintainer="benoit.herard@orange.com"

RUN apt update;\
    apt install -y ipmitool libc-dev gcc; \
    pip3 install --no-cache-dir --upgrade pip; \
    cd /usr/local;\
    git clone https://github.com/bherard/energyrecorder;\
    cd energyrecorder;\
    pip3 install -r server-collector/requirements.txt

RUN apt-get clean && \ 
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT cd /usr/local/energyrecorder/server-collector && export PYTHONPATH=.:$PYTHONPATH && python daemon.py
