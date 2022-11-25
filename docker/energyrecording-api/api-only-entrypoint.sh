#!/bin/bash

PORT=8000
WORKERS=$(expr $(nproc) + 1)

while [ "$1" != "" ] ; do
    echo $1
    if [ "$1" == "-h" ] ; then
        usage
    elif [ "$1" == "-p" ] ; then
        shift
        PORT=$1
    elif [ "$1" == "-w" ] ; then
        shift
        WORKERS=$1
    fi
    shift
done

echo "Starting with:"
echo "Workers=$WORKERS"
echo "Port=$PORT"

cd $HOME/energyrecorder/recording-api
gunicorn -b 0.0.0.0:$PORT -w $WORKERS app:APP