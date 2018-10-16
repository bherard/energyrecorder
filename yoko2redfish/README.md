# yoko2redfish
Request YOKOGAWA powermeter with redfish API

This module run a web server responding as a (sub part of) RedFish API to query power on YOKOGAWA Pometers as a unique server.
It's based on https://github.com/intel/yoko-tool

It's written in python2.7.

# Install
This section explain how to install yoko2redfish a linux (debian) box.
But you can aloso use it as a docker container (see bellow).

**NOTE:** This install mode does not describe how to use this Flask APP with nginx or apache. 
If required, prefer docker mode

## pre requisite
  * install python/python virtual env
  * install yoko-tool as described here https://github.com/intel/yoko-tool

## install software and configuration
Clone this repo:

```bash
git clone https://github.com/bherard/energyrecorder.git
```
go to conf folder and create config files
```bash
cd energyrecorder/yoko2redfish/conf

# Logs configuration
cp webapp-logging.conf.sample webapp-logging.conf

#App configuration
cp webapp-settings.yaml.sample webapp-settings.yaml
```

## Launch
Check configuration as described bellow and launch the server:
```bash
cd <folder-where-energyrecord-is-cloned>/yoko2redfish
python app.py
```
**NOTE:** This launch a threaded flask server witch not recommanded for heavy load. In our case, load should be low, but  this way of working is not recommended as best practice with flask server.
It should be used with apache or nginx instead.
If you prefer this second way of doing, please refer to docker install mode.

# Docker

yoko2redfish can be used as a docker container. 

Configuration is quite easy:
  * Create a local folder to handel config
  * Launch container with mapping powermeter(s)
  
## Local config

Create a local folder for configuration and create config files (and optionaly a log folder):
```bash
mkdir -p yoko2redfish/conf
mkdir -p yoko2redfish/log
curl https://raw.githubusercontent.com/bherard/energyrecorder/master/yoko2redfish/conf/webapp-logging.conf.sample -o yoko2redfish/conf/webapp-logging.conf
curl https://raw.githubusercontent.com/bherard/energyrecorder/master/yoko2redfish/conf/webapp-settings.yaml.sample -o yoko2redfish/conf/webapp-settings.yaml
```
Check config files as described bellow

## Launch
```bash
docker run -d --device /dev/usbtmc1:/dev/usbtmc1 -v <your-location>/yoko2redfis/conf:/usr/local/yoko2redfish/conf [-v <your-location>/yoko2redfis/log:/var/log/yoko2redfish [-p 80:80] --name yoko2redfish bherard/yoko2redfish
```
  * use `-v <your-location>/yoko2redfis/log:/var/log/yoko2redfish` if you want to see log from host (see `-v` docker doc). 
  * use `-p 80:80` to connect redfish pseudo server with host IP on port 80 (see `-p` docker doc)
# Config files
Before installing, this section describe the configuration (what ever the install mode is)

## Log config
The log configuration is controled by webapp-logging.conf
In this file  with the line:
```
args=('/var/log/yoko2redfish/yoko2redfish.log', 'a', 100 * 1024 *1024 , 5,)
```
you can set the output log file (here: /var/log/yoko2redfish/yoko2redfish.log) and its size (here 100M).
We recommend you to not change filename in docker mode unless you are aware of what you are doing.

## App config

  Parameters `BIND`: Define here the listening IP and port when app is lauched directly with python  
  Parameters `YOKOTOOL_PATH` : location where yoko-tool where cloned. **DO NOT CHANGE IT IN DOCKER INSTALL MODE**
  Parameters `POWERMETERS`: List of powermeters to aggregate as unique measurement.


Powermeter definition:

`dev`: physical powermeter in /dev ex: /dev/usbtmc1

`pmtype`: powermeter type (wt310|wt210 see https://github.com/intel/yoko-tool)

# Use
Once server is configured, use it as regular redfish host from server-collector config
For host, use the ip-or-name:port where flask server is bind (app launched as standalone flask server).

In case of docker depending on the way you launched the container (`-p` parameter) you'll have to use:
  * hostname-or-ip-of-host (with -p 80:80)
  * hostname-or-ip-of-host:port (with -p port:80)
  * container-ip (not -p parameter)

Ex.:
```
PODS:
 - environment: TEST-YOKO
   servers:
   - host: 192.168.2.22
     id: my-server
     type: redfish
     user:
     pass:
     polling_interval: 1

