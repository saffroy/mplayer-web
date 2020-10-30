#!/usr/bin/env python3

import datetime
import flask
import functools
import mplayer
import os
import re
import werkzeug.exceptions

VIDEOS_RE = re.compile('.*\.(mkv|avi|mpg|mp4|iso)$',
                       flags=re.IGNORECASE)

def all_files(dirs):

    def gen_files(dirs):
        for topdir in dirs:
            for dirname, subdirs, filenames in os.walk(topdir):
                for filename in filenames:
                    if VIDEOS_RE.match(filename):
                        yield os.path.join(dirname, filename)

    return sorted(list(gen_files(dirs)))

TOP_DIRS = ['/backup/tmp/', '/home/saffroy/pvr']
ALL_FILES = []
FILE_INDEX = 0

player = None

class PlayerWrapper(mplayer.Player):
    def __init__(self, *args, **kwargs):
        mpargs = kwargs.get('args', ())
        mpargs += ('-msglevel', 'global=6')
        mpargs += ('-v',) * 5
        kwargs['args'] = mpargs

        super(PlayerWrapper, self).__init__(*args, **kwargs)

def init():
    global player

    if player is not None:
        player.quit()
        player = None

    filename = ALL_FILES[FILE_INDEX]
    args = ()
    if re.search('\.iso$', filename):
        args += ('-dvd-device', filename)
        target = 'dvd://'
    else:
        args += ('-utf8',)
        target = filename

    try:
        suffix = filename.split('.')[-1]
        base = filename.rstrip(suffix)
        with open(base + 'delay') as f:
            d = f.read().strip()
            args += ('-subdelay', d)
    except:
        pass

    player = PlayerWrapper(args=args)
    player.loadfile(target)

    player.fullscreen = True
    player.sub_select(0)
    player.osd(1)
    player.volume = 5
    player.time_pos = 0
    player.osd_show_property_text(os.path.basename(filename), 3000)

def get_state(player):
    if player is None:
        return dict()
    return {
        'now': datetime.datetime.now().isoformat(),
        'filename': player.filename,
        'fullscreen': player.fullscreen,
        'sub': player.sub,
        'osd': player.osdlevel,
        'paused': player.paused,
        'volume': player.volume,
        'mute': player.mute,
        'time': player.time_pos,
        'audio_track': player.switch_audio,
    }

app = flask.Flask('mplayer-web')

@app.route('/')
def root():
    if player is None:
        global ALL_FILES
        files = all_files(TOP_DIRS)
        ALL_FILES = ['dvd://'] + files

        filenames = enumerate(['DVD'] +
                              list(map(os.path.basename, files)))
        page = flask.render_template(
            'browse.html',
            filenames=filenames,
            selected=FILE_INDEX,
        )
    else:
        page = flask.render_template(
            'play.html',
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
        return ''
    except:
        raise werkzeug.exceptions.BadRequest(
            'Error: bad value for param "idx": "{}"'.format(idx))

@app.route('/state')
def state():
    return flask.jsonify(get_state(player))

def pcommand(fun):
    @functools.wraps(fun)
    def real_fun(*args, **kwargs):
        if player is not None:
            fun(*args, **kwargs)
        return ''
    return real_fun

@app.route('/pause')
@pcommand
def pause():
    player.osd_show_progression()
    player.pause()

@app.route('/vol_inc')
@pcommand
def vol_inc():
    v = round(player.volume + 5)
    player.volume = v
    player.osd_show_property_text('Vol: {}'.format(v), 1000)

@app.route('/vol_dec')
@pcommand
def vol_dec():
    v = round(max(0, player.volume - 5))
    player.volume = v
    player.osd_show_property_text('Vol: {}'.format(v), 1000)

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
@pcommand
def start():
    init()

@app.route('/sub')
@pcommand
def sub():
    player.sub_select()

@app.route('/fwd')
@pcommand
def fwd():
    player.seek(10)

@app.route('/back')
@pcommand
def back():
    player.seek(-10)

@app.route('/ffwd')
@pcommand
def ffwd():
    player.seek(60)

@app.route('/fback')
@pcommand
def fback():
    player.seek(-60)

@app.route('/fffwd')
@pcommand
def fffwd():
    player.seek(600)

@app.route('/ffback')
@pcommand
def ffback():
    player.seek(-600)

def probe_audio_tracks(track_nums):
    # track numbers aren't sequential, probe for the next
    for t in track_nums:
        player.switch_audio = t
        if player.switch_audio == t:
            break

@app.route('/audio_next')
@pcommand
def audio_next():
    x = player.volume
    track = player.switch_audio
    probe_audio_tracks(range(track+1, track+10, 1))
    player.volume = x

@app.route('/audio_prev')
@pcommand
def audio_prev():
    x = player.volume
    track = player.switch_audio
    probe_audio_tracks(range(track-1, track-10, -1))
    player.volume = x

@app.route('/next')
@pcommand
def next():
    stop()
    global FILE_INDEX
    FILE_INDEX += 1
    init()
