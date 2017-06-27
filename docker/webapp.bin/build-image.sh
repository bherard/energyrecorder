#!/bin/bash
#curl -s https://raw.githubusercontent.com/bherard/energyrecorder/master/docker/webapp.dockerfile |docker build -t energyrecorder/webapp -
cat ../webapp.dockerfile |docker build -t energyrecorder/webapp -
