#!/bin/bash
cd `dirname $0`/..
source venv/bin/activate
export PYTHONPATH=.:$PYTHONPATH
cd web.py/
../venv/bin/python app.py
