#!/bin/bash

. ./energy.sh



energy-recorder-begin-session "TEST"

echo "Program is startig"
sleep 1

energy-recorder-set-step "Step1"
echo "program at step 1"
sleep 1

energy-recorder-set-step "Step2"
echo "program at step 2"
sleep 1

energy-recorder-finish-session
