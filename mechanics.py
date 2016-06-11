# -*- coding: utf-8 -*-
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol, task
from twisted.internet import fdesc, defer, error
from datetime import datetime, date

from random import randint
from datetime import time, tzinfo, timedelta
from copy import copy
import random
from sexpdata import loads, dumps, Symbol
from functools import partial

class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


COMMANDS = {
    "reset" : 'reset',
    "players" : 'players',
    "words" : 'words',
    "guesses" : 'guesses',
    "winner" : 'winner',
    "correct" : 'correct',
    "total_time" : 'total_time',
    "tick" : 'tick',
}

def dump_command(command, *args):
    res = [Symbol(command),]
    if len(args) != 0: res.extend(args)
    return dumps(res)


cmd = Bunch(**{
    y : partial(dump_command, z) for y,z in COMMANDS.iteritems()
}) #wow

def process_line(line):
    raw = line[:-1].split(",")
    img = None
    if len(raw) == 3:
        img = prep_img(raw[2])
    return {
        "word" :  raw[1].decode("utf-8"),
        "pic"  :  img,
        "trans":  raw[0].decode("utf-8"),
        "guess":  u"",}

def process_dict(data):
    return [process_line(line) for line in data]

data = read_whole_dict("words")
total_words = process_dict(data)


# def countdown_remaining_time():
#     global remaining_time
#     global rem
#     global progress_percent
#     #datetime.time can't do arithmetics, horrible code below
#     if not remaining_time.hour and not remaining_time.minute and not remaining_time.second:
#         t_lb_surface.fill(DEFEAT_TABLE_COLOR)
#         rem.stop()
#         task.deferLater(reactor, 2, reset_game)
#         show_correct(WORDS)
#         return
#     td = date.today()
#     remaining_time = datetime.combine(td, remaining_time) - datetime.combine(td, time(0, 0, 1))
#     hours, remainder = divmod(remaining_time.seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     remaining_time = time(hours, minutes, seconds)
#     progress_percent -= BAR_TICK

# rem = LoopingCall(countdown_remaining_time)
# rem.start(1)

# reactor.run()
