# yoko2redfish
Request YOKOGAWA powermeter with redfish API

This module run a web server responding as a (sub part of) RedFish API to query power on YOKOGAWA Pometers as a unique server.
It's based on https://github.com/intel/yoko-tool

It's written in python2.7.

# install
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

# Config files
Before installing, this section describe the configuration (what ever the install mode is)

## Log config
The log configuration is controled by webapp-logging.conf
In this file  with the line:
```
args=('/var/log/yoko2redfish/yoko2redfish.log', 'a', 100 * 1024 *1024 , 5,)
```
you can set the output log file (here: /var/log/yoko2redfish/yoko2redfish.log) and its size (here 100M)

## App config

  Parameters `BIND`: Define here the listening IP and port when app is lauched directly with python  
  Parameters `YOKOTOOL_PATH` : location where yoko-tool where cloned. **DO NOT CHANGE IT IN DOCKER INSTALL MODE**
  Parameters `POWERMETERS`: List of powermeters to aggregate as unique measurement.


Powermeter definition:

`dev`: physical powermeter in /dev ex: /dev/usbtmc1

`pmtype`: powermeter type (wt310|wt210 see https://github.com/intel/yoko-tool)


