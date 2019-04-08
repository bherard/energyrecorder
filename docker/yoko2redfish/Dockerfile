FROM alpine
LABEL maintainer="benoit.herard@orange.com"

EXPOSE 80/tcp

RUN apk --update add sudo curl git python3 py3-pip bash uwsgi-python3 nginx;\
    pip install --upgrade pip; \
    mkdir -p /usr/local/yoko2redfish; \
    cd /usr/local;\
    git clone https://github.com/intel/yoko-tool.git;\
    cd /tmp;\
    git clone https://github.com/bherard/energyrecorder.git;\
    mv /tmp/energyrecorder/yoko2redfish /usr/local;\
    curl https://raw.githubusercontent.com/bherard/energyrecorder/master/docker/yoko2redfish/yoko2redfish-entrypoint.sh -o /entrypoint.sh;\
    chmod u+x /entrypoint.sh;\
    cd /usr/local/yoko2redfish;\
    pip install -r requirements.txt;\
    chmod u+x /entrypoint.sh;\
	echo DONE

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
