#!/bin/bash

# Copyright (c) 2017 Orange and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

# Set of function to use Energy Monitoring API

LOG_DEBUG=3
LOG_INFO=2
LOG_WARNING=1
LOG_ERROR=0

ENERGY_LOG_LEVEL=$LOG_ERROR

INITIAL_STEP="running"

# Logging base function
# parameters:
#   $1: Log level ("DEBUG"|"INFO"|"WARNING"|"ERROR")
#   $2....$n: data to log
function energy-log(){

  D=`date "+%x %T"`
  LEVEL=$1
  shift
  echo "$D - energy - $LEVEL - "$* >&2
}

# Log DEBUG messages
# parameters:
#   $1.....$n: data to log
function energy-log-debug(){
  if [ $ENERGY_LOG_LEVEL -ge $LOG_DEBUG ] ; then
    energy-log "DEBUG" $*
  fi
}
# Log INFO messages
# parameters:
#   $1.....$n: data to log
function energy-log-info(){
  if [ $ENERGY_LOG_LEVEL -ge $LOG_INFO ] ; then
    energy-log "INFO" $*
  fi
}
# Log WARNING messages
# parameters:
#   $1.....$n: data to log
function energy-log-warning(){
  if [ $ENERGY_LOG_LEVEL -ge $LOG_WARNING ] ; then
    energy-log "WARINIG" $*
  fi
}
# Log ERROR messages
# parameters:
#   $1.....$n: data to log
function energy-log-error(){
  energy-log "ERROR" $* >&2
}

# Submit a complet scenrio to recording API
# parameters:
#   $1: scenario name
#   $2: step name
function energy-recorder-submit-scenario(){
  if [ $DO_RECORDING -eq 1 ] ; then
    energy-log-debug "Submiting scenario '$1' at step '$2'"
    payload=`echo '{"step": "'$2'", "scenario": "'$1'"}'`
    url=`echo $ENERGY_API_URL"/recorders/environment/"$ENERGY_ENVIRONMENT_NAME`
    curl -i -k -s $API_AUTH -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$payload" "$url">/tmp/$$.curl
    grep "200 OK" /tmp/$$.curl >/dev/null
    if [ $? -ne 0 ] ; then
      energy-log-error "Error while submitting scenario"
      cat /tmp/$$.curl >&2
    else
      energy-log-debug "Scenario '$1' at step '$2' submitted"
    fi
    rm /tmp/$$.curl
  fi
}

# Set step for current scenario
# parameters:
#   s1: step name
function energy-recorder-set-step(){
  if [ $DO_RECORDING -eq 1 ] ; then
    energy-log-debug "Setting step to '$1'"
    payload=`echo '{"step": "'$1'"}'`
    url=`echo $ENERGY_API_URL"/recorders/environment/"$ENERGY_ENVIRONMENT_NAME/step`
    curl -i -k -s $API_AUTH -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d "$payload" "$url">/tmp/$$.curl
    grep "200 OK" /tmp/$$.curl >/dev/null
    if [ $? -ne 0 ] ; then
      energy-log-error "Error while setting step"
      cat /tmp/$$.curl >&2
    else
      energy-log-debug "Step set to '$1'"
    fi
    rm /tmp/$$.curl
  fi
}

# Set CURRENT_SCENARIO and CURRENT_STEP env vars for current scenario defined
# for environment in recording API
# parameters:
#   none
function energy-recorder-get-current-scenario(){
  if [ $DO_RECORDING -eq 1 ] ; then
    energy-log-debug "Getting current scenario"

    CURRENT_SCENARIO=""
    CURRENT_STEP=""
    url=`echo $ENERGY_API_URL"/recorders/environment/"$ENERGY_ENVIRONMENT_NAME`
    curl -i -k -s $API_AUTH --header 'Accept: application/json' "$url">/tmp/$$.curl
    grep "404 NOT FOUND" /tmp/$$.curl >/dev/null
    if [ $? -eq 0 ] ; then
      energy-log-debug "No current running scenario at $url"
    else
      grep "200 OK" /tmp/$$.curl >/dev/null
      if [ $? -ne 0 ] ; then
        energy-log-error "Error while getting current scenario"
        cat /tmp/$$.curl >&2
      else
        CURRENT_SCENARIO=`cat /tmp/$$.curl | grep '"scenario":'| awk '{print $6}'|sed 's/\"//g'|sed 's/\}//g'`
        CURRENT_STEP=`cat /tmp/$$.curl | grep '"step":'| awk '{print $4}'|sed 's/\"//g'|sed 's/\,//g'`
      fi

    fi
    rm /tmp/$$.curl
  fi
}


# Stop recording session
# parameters:
#   none
function energy-recorder-stop(){
  if [ $DO_RECORDING -eq 1 ] ; then
    energy-log-debug "Stoping recording"
    url=`echo $ENERGY_API_URL"/recorders/environment/"$ENERGY_ENVIRONMENT_NAME`
    curl -i -k -s $API_AUTH -X DELETE --header 'Accept: application/json'  "$url">/tmp/$$.curl
    grep "200 OK" /tmp/$$.curl >/dev/null
    if [ $? -ne 0 ] ; then
      energy-log-error "Error while stoping recording"
      cat /tmp/$$.curl >&2
    else
      energy-log-debug "Recording is stoppped"
    fi
    rm /tmp/$$.curl
  fi
}

# Stop recording session
# parameters:
#   $1: Starting scenario name
function energy-recorder-start(){
  if [ $DO_RECORDING -eq 1 ] ; then
    energy-log-debug "Starting recording for scenario '$1'"
    energy-recorder-submit-scenario $1 $INITIAL_STEP
  fi
}


# Ends a recording session by reseting recording API as same state at it was
# when  energy-recorder-begin-session was called (reset to $CURRENT_SCENARIO
# and $CURRENT_STEP if required)
# parameters:
#   none
function energy-recorder-finish-session(){
  if [ $DO_RECORDING -eq 1 ] ; then
    CURRENT_SCENARIO=$STORED_SCENARIO
    CURRENT_STEP=$STORED_STEP
    if [ "$CURRENT_SCENARIO" == "" -o "$CURRENT_STEP" == "" ] ; then
      energy-recorder-stop
    else
      energy-recorder-submit-scenario "$CURRENT_SCENARIO" "$CURRENT_STEP"
    fi
  fi
}

# Starts a recording session by storing current state for recording API
# parameters:
#   none
function energy-recorder-begin-session(){
  if [ $DO_RECORDING -eq 1 ] ; then
    energy-recorder-get-current-scenario
    STORED_SCENARIO=$CURRENT_SCENARIO
    STORED_STEP=$CURRENT_STEP
    energy-recorder-start "$1"
  fi
}


# Load conf and intialize lib
DO_RECORDING=1
if [ -f "energy.conf" ] ; then
  #conf exists, load it
  . ./energy.conf

  # and check if it's valid
  if [ "$ENERGY_ENVIRONMENT_NAME" == "" ] ; then
    energy-log-error "ENERGY_ENVIRONMENT_NAME variable not set or empty"
    DO_RECORDING=0
  fi
  if [ "$ENERGY_API_URL" == "" ] ; then
    energy-log-error "ENERGY_API_URL variable not set or empty"
    DO_RECORDING=0
  fi
  if [ "$ENERGY_API_USER" != "" -a "$ENERGY_API_PASSWORD" != "" ] ; then
    API_AUTH='-u "'$ENERGY_API_USER':'$ENERGY_API_PASSWORD'"'
  else
    API_AUTH=""
  fi
  if [ $DO_RECORDING -eq 1 ] ; then
    curl -k -s --connect-timeout 1 -X GET --header 'Accept: application/json' $API_AUTH "$ENERGY_API_URL/monitoring/ping"| grep OK 2>&1 > /dev/null
    if [ $? -ne 0 ] ; then
      energy-log-error "Recording API is not available: recording will not be done"
      DO_RECORDING=0
    else
      energy-log-info "Configuration is valid: recording should be done"
    fi
  fi
else
  energy-log-error "energy.conf file not found: no energy API support!"
  DO_RECORDING=0
fi
