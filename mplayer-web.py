#!/usr/bin/env python3

import datetime
import flask
import functools
import json
import mplayer
import os
import re
import werkzeug.exceptions

VIDEOS_RE = re.compile('.*\.(mkv|avi|mpg|mp4)$', flags=re.IGNORECASE)

def all_files(dirs):

    def gen_files(dirs):
        for topdir in dirs:
            for dirname, subdirs, filenames in os.walk(topdir):
                for filename in filenames:
                    if VIDEOS_RE.match(filename):
                        yield os.path.join(dirname, filename)

    return sorted(list(gen_files(dirs)))

TOP_DIRS = ['/backup/tmp/']
ALL_FILES = []
FILE_INDEX = 0

player = None

def init():
    global player

    if player is not None:
        player.quit()
        player = None

    player = mplayer.Player()
    filename = ALL_FILES[FILE_INDEX]
    player.loadfile(filename)

    player.fullscreen = True
    player.sub_select(0)
    player.osd(1)
    player.volume = 5
    player.time_pos = 0

def get_state(player):
    return {
        'now': datetime.datetime.now().isoformat(),
        'fullscreen': player.fullscreen,
        'sub': player.sub,
        'osd': player.osdlevel,
        'paused': player.paused,
        'volume': player.volume,
        'mute': player.mute,
        'time': player.time_pos,
    }

app = flask.Flask('mplayer-web')

@app.route('/')
def root():
    if player is None:
        global ALL_FILES
        ALL_FILES = all_files(TOP_DIRS)

        page = flask.render_template(
            'browse.html',
            filenames=enumerate(map(os.path.basename, ALL_FILES)),
            selected=FILE_INDEX,
        )
    else:
        page = flask.render_template(
            'play.html',
            state=json.dumps(get_state(player)),
        )
    return page

@app.route('/select')
def select():
    idx = flask.request.args.get('idx', '0')
    try:
        _idx = int(idx)
        fname = ALL_FILES[_idx]

        global FILE_INDEX
        FILE_INDEX = _idx
        init()
    except:
        raise werkzeug.exceptions.BadRequest(
            'Error: bad value for param "idx": "{}"'.format(idx))

def pcommand(fun):
    @functools.wraps(fun)
    def real_fun(*args, **kwargs):
        if player is not None:
            fun(*args, **kwargs)
        if player is not None:
            return flask.jsonify(get_state(player))
        else:
            return flask.jsonify(dict())
    return real_fun

@app.route('/pause')
@pcommand
def pause():
    player.pause()

@app.route('/vol_inc')
@pcommand
def vol_inc():
    player.volume += 5

@app.route('/vol_dec')
@pcommand
def vol_dec():
    player.volume = max(0, player.volume - 5)

@app.route('/mute')
@pcommand
def mute():
    player.mute = not(player.mute)

@app.route('/osd')
@pcommand
def osd():
    player.osd()

@app.route('/fullscreen')
@pcommand
def fullscreen():
    player.fullscreen = not(player.fullscreen)

@app.route('/stop')
@pcommand
def stop():
    global player
    player.quit()
    player = None

@app.route('/start')
def start():
    init()
    return flask.jsonify(get_state(player))

@app.route('/sub')
@pcommand
def sub():
    player.sub_select()

@app.route('/fwd')
@pcommand
def fwd():
    player.time_pos += 10

@app.route('/back')
@pcommand
def back():
    player.time_pos = max(0, player.time_pos-10)
