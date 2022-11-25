FROM python:3.9
LABEL maintainer="benoit.herard@orange.com"

RUN addgroup recording-api && \
    useradd  -m recording-api -g recording-api && \
    mkdir -p /var/log/energyrecorder && \
    chown recording-api:recording-api  /var/log/energyrecorder && \
    apt update && \
    apt install -y vim 

ADD api-only-entrypoint.sh /entrypoint.sh

USER recording-api

RUN cd $HOME && \
    git clone https://github.com/bherard/energyrecorder

USER root

RUN cd /home/recording-api/energyrecorder/recording-api/ &&\
    pip install -r requirements.txt && \
    cd conf && \
    cp webapp-logging.conf.sample webapp-logging.conf && \
    cp webapp-settings.yaml.sample webapp-settings.yaml

USER recording-api

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
