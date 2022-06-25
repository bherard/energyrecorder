# energyrecorder

This repo contains 2 components to collect and store metrics for various hardware, mùainly usin snmp and RedFish

* server-collector: Poller with protocols adapter to connect data on equipements
* recording-api: Rest API to receive data form pollers and store in an Influx database

In addition, it also provide a wapper for Yko watt meter connected with USB to publish mesurement as RedFish API (only power meter is supported for RedFish API)

Both are available as docker images on dockerhub (https://hub.docker.com/r/bherard)

This code is the implementation of the Sensors Recording API and sensors collecting poller

More information available at https://wiki.opnfv.org/display/testing/Power+consumption+monitoring

## recording-api

API is available on dockerhub with `bherard/energyrecorder-api`.

Container mais be started with following parameters:
- -proxy: When stating, container download some additional config files. If container can't connect internet directly define proxy to use with this flag.
- -nofinflux: Embed InfluxDB server is not configured nor started with API. (if set, you have to manulaly configure API DB Conenction parameters).
- -admin-user USER: Influx DB admin user name (all privileges).
- -admin-password PASS: Password for admin user.
- -readonly-username USER: Influx DB user name with read on privileges.
- -readonly-password PASS: Password for read only user name.

**NOTE**:
- -admin-user, -admin-password, -readonlyuser and -readonly-password should be set all together or none of them.
- -admin-user, -admin-password, -readonlyuser and -readonly-password make no sens with -noinflux.

**VOLUME MOUNT (useful path in the container to bind as  volume)**:
- influxDB configuration is located in /etc/influxdb/influxdb.conf
- influxDB data is located in /var/lib/influxdb/
- API config files (incl. logging) is located in /usr/local/energyrecorder/recording-api/conf/
-- API logs are located in /var/log/energyrecorder

**LISTENING PORT:**
- API is listening on port 80 (Swagger for API available at http://container/resources/doc/ )
- Influx is listening on port 8086

Basic example of start command with docker:
```bash
    docker start -d --name energyrecorder-api \
    -v /path/on/host/for/influx/data:/var/lib/influxdb/ \
    -v /path/on/host/for/influx/config:/etc/influxdb/ \
    - /path/on/host/for/api/config:/usr/local/energyrecorder/recording-api/conf/
    -v /path/on/host/for/api/logs:/var/log/energyrecorder \
    -p 80:80 \
    -p 8086:8086 \
    --restart always \
    bherard/energyrecorder-api \
    -admin-user admin \
    -admin-password admin-password \
    -readonly-user reader \
    -readonly-password reader-password
```


