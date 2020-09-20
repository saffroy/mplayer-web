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

TOP_DIRS = ['/backup/tmp/The Good Place Season 3 Complete 720p AMZN WEBRip x264 [i_c]']
ALL_FILES = all_files(TOP_DIRS)
FILE_INDEX = 0

p = None
filename = '/backup/tmp/The Good Place Season 3 Complete 720p AMZN WEBRip x264 [i_c]/The Good Place S03e01 Everything Is Bonzer!.mkv'

def init():
    global p

    if p is not None:
        p.quit()
        p = None

    p = mplayer.Player()
    filename = ALL_FILES[FILE_INDEX]
    p.loadfile(filename)

    # p.pause()

    p.fullscreen = True
    p.sub_select(0)
    p.osd(1)
    p.volume = 5
    p.time_pos = 0


def get_state(p):
    return {
        'now': datetime.datetime.now().isoformat(),
        'fullscreen': p.fullscreen,
        'sub': p.sub,
        'osd': p.osdlevel,
        'paused': p.paused,
        'volume': p.volume,
        'mute': p.mute,
        'time': p.time_pos,
    }

app = flask.Flask('mplayer-web')

@app.route('/')
def root():
    if p is None:
        page = flask.render_template(
            'browse.html',
            filenames=enumerate(map(os.path.basename, ALL_FILES)),
            selected=FILE_INDEX,
        )
    else:
        page = flask.render_template(
            'play.html',
            state=json.dumps(get_state(p)),
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
        global p
        if p is not None:
            fun(*args, **kwargs)
        if p is not None:
            return flask.jsonify(get_state(p))
        else:
            return flask.jsonify(dict())
    return real_fun

@app.route('/pause')
@pcommand
def pause():
    global p
    p.pause()

@app.route('/vol_inc')
@pcommand
def vol_inc():
    global p
    p.volume += 5

@app.route('/vol_dec')
@pcommand
def vol_dec():
    global p
    p.volume = max(0, p.volume - 5)

@app.route('/mute')
@pcommand
def mute():
    global p
    p.mute = not(p.mute)

@app.route('/osd')
@pcommand
def osd():
    global p
    p.osd()

@app.route('/fullscreen')
@pcommand
def fullscreen():
    global p
    p.fullscreen = not(p.fullscreen)

@app.route('/stop')
@pcommand
def stop():
    global p
    p.quit()
    p = None

@app.route('/start')
def start():
    init()
    return flask.jsonify(get_state(p))

@app.route('/sub')
@pcommand
def sub():
    global p
    p.sub_select()

@app.route('/fwd')
@pcommand
def fwd():
    global p
    p.time_pos += 10

@app.route('/back')
@pcommand
def back():
    global p
    p.time_pos = max(0, p.time_pos-10)
