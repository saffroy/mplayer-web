#!/bin/bash

set -x

cd $(dirname $0)
. venv3/bin/activate

export DISPLAY=${DISPLAY:-:0}

LC_ALL=C.UTF-8 LANG=C.UTF-8 \
      FLASK_DEBUG=1 \
      FLASK_APP=mplayer-web.py \
      flask run --host 0.0.0.0 --port 8081 "$@"
