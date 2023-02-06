#!/bin/bash

set -x

cd $(dirname $0)
. venv3/bin/activate

export DISPLAY=${DISPLAY:-:0}

LC_ALL=C.UTF-8 LANG=C.UTF-8 \
      FLASK_DEBUG=0 \
      FLASK_APP=mplayer-web.py \
      exec flask run --port 8081 "$@"
