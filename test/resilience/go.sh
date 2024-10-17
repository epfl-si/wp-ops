#!/bin/bash
VENV=wpresi

if [ -z "$VIRTUAL_ENV" ] ; then
  [ -d $VENV ] || python3 -m venv $VENV
  source wpresi/bin/activate
fi
python3 -m pip install kubernetes requests

f=mplp_$(date +%F_%s)
python3 mariadb-petlepod-downtime.py >$f.out.json 2>$f.err

