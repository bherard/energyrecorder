FROM influxdb:1.8.10-alpine
LABEL maintainer="benoit.herard@orange.com"


EXPOSE 80/tcp
EXPOSE 8086/tcp

RUN apk --update add git python3 py3-pip bash ca-certificates curl uwsgi-python3 nginx &&\
    update-ca-certificates &&\
    apk add openssl &&\
    pip3 install --upgrade pip &&\
    cd /usr/local/ &&\
    git clone https://github.com/bherard/energyrecorder &&\
    cd energyrecorder &&\
    pip install -r recording-api/requirements.txt &&\
    mv /entrypoint.sh /influx-entrypoint.sh && \
    addgroup recording-api && \
    adduser -D -G recording-api recording-api

ADD recording-api-entrypoint.sh /entrypoint.sh
RUN curl https://raw.githubusercontent.com/bherard/energyrecorder/master/docker/energyrecording-api/recording-api-entrypoint.sh -o /entrypoint.sh &&\
	chmod u+x /entrypoint.sh &&\
	wget https://raw.githubusercontent.com/bherard/energyrecorder/master/influx/create-certs.sh -O /usr/local/bin/create-certs.sh &&\
	chmod u+x /usr/local/bin/create-certs.sh &&\
	echo DONE


ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
