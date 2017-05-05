#!/bin/bash
cd `dirname $0`/..
source venv/bin/activate
export PYTHONPATH=.:$PYTHONPATH
cd server-collector/
../venv/bin/python daemon.py
