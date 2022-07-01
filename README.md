# energyrecorder

This repo contains 2 components to collect and store metrics for various hardware, mùainly usin snmp and RedFish

* server-collector: Poller with protocols adapter to connect data on equipements
* recording-api: Rest API to receive data form pollers and store in an Influx database

In addition, it also provide a wapper for Yko watt meter connected with USB to publish mesurement as RedFish API (only power meter is supported for RedFish API)

Both are available as docker images on dockerhub (https://hub.docker.com/r/bherard)

This code is the implementation of the Sensors Recording API and sensors collecting poller

More information available at https://wiki.opnfv.org/display/testing/Power+consumption+monitoring

## recording-api

API is available on dockerhub with `bherard/energyrecorder-api` as a ready to use image.

Container mais be started with following parameters:
- -port: API Listening port (default 8080)
- -proxy: When stating, container download some additional config files. If container can't connect internet directly define proxy to use with this flag.
- -nofinflux: Embeded InfluxDB server is not configured nor started with API. (if set it, you have to manualy configure API DB Connection parameters in `webapp-settings.yaml` (see **VOLUME MOUNT** below ).
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
- API is listening on port 8080 (Swagger for API available at http://container:8080/resources/doc/ )
- Influx is listening on port 8086

Basic example of start command with docker:
```bash
    docker start -d --name energyrecorder-api \
    -v /path/on/host/for/influx/data:/var/lib/influxdb/ \
    -v /path/on/host/for/influx/config:/etc/influxdb/ \
    -v /path/on/host/for/api/config:/usr/local/energyrecorder/recording-api/conf/
    -v /path/on/host/for/api/logs:/var/log/energyrecorder \
    -p 80:8080 \
    -p 8086:8086 \
    --restart always \
    bherard/energyrecorder-api \
    -admin-user admin \
    -admin-password DEFINE-YOURS \
    -readonly-user reader \
    -readonly-password DEFINE-YOURS
```
### Config file (webapp-settings.yaml)
```yaml
INFLUX:
    host: "http://localhost:8086" #InfluxDB host and protocol
    db: "NRG" # API DB
    user: "influx-write-user" # Influx User with write privileges (if auth enabled)
    pass: "influx-write-user-pass" #  Influx User's password (if auth enabled)

# Optional: Set ALWAYS_RECORD to True to record Servers comnsuption even 
# if no running scenario found, else data comming form equipments are only recorded if a scenario is running (Default True)
ALWAYS_RECORD : False

# Optional - republish received data on MQTT (SSL not supported)
MQTT: 
    host: localhost # MQTT Host
    port: 1883 # Optional, MQTT Port (default 1883)
    user: mqtt-user # If auth enabled
    pass: mqqt-user-pass # If auth enabled
    base_path: nrj4it # Optional, Topic prefix (without ending /) (default empty)

```
## collector

Collector is available on dockerhub with `bherard/energyrecorder-collector` as a ready to use image.

### Config file structure

Config file contains 2 main sections:
- equipments to poll (see `PODS` in sample config file)
- API connection parameters (see `RECORDER_API_SERVER`)

#### API Connection parameters
Ex:
```yaml
RECORDER_API_SERVER:
  base_url: https://recordingapi.myserver.com
  user: 'jdoe'
  pass: 'ipsum-lorem'
  verify_cert: True
  timeout: 5
  proxy: http://my-proxy:3128
```

where:
- `base_url`: server where recording API is running
- `user`: basic authentication user to use to connect recoding API (leave empty if not protected)
- `pass`: basic authentication user's password to use to connect recoding API (leave empty if not protected)
- `verify_cert`: Optional (default True). Allow to disable SSL Certs verification (issuer, hostname...) when connection API with https
- `timeout`: Optional (default 2) Timeout in sec. to send data to recording API.
- `proxy`: Optional. http proxy to use to connect recording API.


### Equiments to poll
The `PODS` section define a list of environnement to poll. The `environnement` key is used to create groups of servers.

Each environnement appears as a tag on measurements in InfluxDB.

An environnement is a list of equipements (servers) to poll.

Environnement settings keys are:
- `environment`: Environment name (as it will appears in Influx)
- `active`: false a true. If false, servers polling is not started when collector starts
- `polling_interval`: Polling interval in seconds.
- `servers`: List of equipements for this env.


Each equipement may use different protocols adapters (type) but share some config settings:
- `id`: Server unique identifier (appears as a tag on measurements in Influx)
- `active`: false a true. If false, server polling is not started when collector starts
- `type`: protocol adapter identifier (see collector config sample file for more details)

The list of supported protocols and the way to configure then is define in the collector settings config file sample [server-collector/conf/collector-settings.yaml.sample](https://github.com/bherard/energyrecorder/blob/master/server-collector/conf/collector-settings.yaml.sample)

## Docker image

You have to setup a collector config befor starting it as container.

For this, first download [server-collector/conf/collector-settings.yaml.sample](https://github.com/bherard/energyrecorder/blob/master/server-collector/conf/collector-settings.yaml.sample) and [server-collector/conf/collector-logging.yaml.sample](https://github.com/bherard/energyrecorder/blob/master/server-collector/conf/collector-logging.yaml.sample) and stor it locally.

Then remove the `.sample` extension and change configuration according to your need.
(our recommandation is to keep /var/log/energyrecorder/server-collector.log for logging location and to create a contaner volume for /var/log/energyrecorder)

Use those files by using their location folder as volume for /usr/local/energyrecorder/server-collector/conf/

Basic example of start command with docker:
```bash
    docker start -d --name energy-collector \
    -v /path/on/host/for/collector/config:/usr/local/energyrecorder/server-collector/ \
    -v /path/on/host/for/collector/logs:/var/log/energyrecorder \
    --restart always \
    bherard/energyrecorder-collector
```

## Recommandation about multi-env

Instead of creating a unique collector container with a configuration for all env. and servers, our recommandation is to create many containers (earch on with a sing env. configuration).

There is multple benefits for this:
- it allow to start or stop polling for an environment idenpendently from the others
- config file  simplyer
- due to Threading limitation with python it allow a better spreading load of polling over all CPU of running host.