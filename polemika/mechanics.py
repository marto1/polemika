# -*- coding: utf-8 -*-
from __future__ import print_function
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol, task
from twisted.protocols.basic import LineReceiver
from twisted.internet import fdesc, defer, error
from twisted.internet.endpoints import TCP4ServerEndpoint
from datetime import datetime, date
from twisted.internet.protocol import Factory

from random import randint
from datetime import time, tzinfo, timedelta
from copy import copy
import random
from sexpdata import loads, dumps, Symbol
from functools import partial
from sys import argv
import string
import logging
import sys

from polemika.misc import setup_logger

fmt = '%(asctime)s %(levelname)s::%(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=fmt)


NUMBER_PLAYERS = 2
TIME = 30 #seconds

class Bunch(object):
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
    "ready" : "ready",
    "error" : "error",
    "disconnected" : "disconnected",
}

def dump_command(command, *args):
    res = [Symbol(command),]
    if len(args) != 0: res.extend(args)
    return dumps(res)

cmd = Bunch(**{
    y : partial(dump_command, z) for y,z in COMMANDS.items()
}) #wow

def read_whole_dict(filename):
    with open(filename, "r") as f:
        data = [line for line in f.readlines()]
    return data

def process_line(line):
    raw = line[:-1].split(",")
    img = ""
    if len(raw) == 3:
        img = raw[2]
    try:
        return {
            "word" :  raw[1],
            "pic"  :  img,
            "trans":  raw[0],}
    except Exception as e:
        print(e)
        raise ValueError(u"Bad line:{0}".format(raw))

def process_dict(data):
    return [process_line(line) for line in data]


def countdown_remaining_time(x=None, state=None):
    if state.remaining_time == 0: return -1
    state.remaining_time -= 1
    return state.remaining_time

def reset_game(x=None, state=None):
    if x == -1: state.phase = "timeout"
    return x

def countdown_task(state):
    res = defer.Deferred()
    res.addCallback(countdown_remaining_time, state)
    res.addCallback(reset_game, state)
    return res

rstr = lambda N: ''.join(random.choice(
    string.ascii_uppercase + string.digits) for _ in range(N))


def equal_words(words, guesses):
    k = 0
    res = []
    for guess in guesses:
        #logging.debug(str(words[k][0]) + guess.decode("utf-8"))
        # .decode("utf-8")
        if words[k][0] == guess:
            res.append(1)
        else:
            res.append(0)
        k += 1
    return res

class GameProtocol(LineReceiver):

    def __init__(self, users, state, log=logging):
        #per object logging
        if log == logging:
            self.log = logging
        else:
            setup_logger(log, log)
            self.log = logging.getLogger(log)
        self.state = state
        self.users = users
        self.name = rstr(10)
        self.users[self.name] = self
        self.phase = "initial"        
        self.handlers = {}
        for k in COMMANDS.keys():
            mname = 'process_{0}'.format(k)
            if getattr(self, mname, None) == None:
                setattr(self, mname, lambda x: x)
            self.handlers[k] = getattr(self, mname)


    def lineReceived(self, line):
        line = line.decode("utf-8")
        self.log.debug("RCVD::" + str(line))
        try:
            rdata = loads(line)
        except Exception as e:
            self.error(10, f"Invalid syntax {e} {line}")
        else:
            if len(rdata) == 0:
                self.error(12, "Empty set")
                return
            if type(rdata[0]) != Symbol:
                self.error(13, "First element is not a symbol")
                return
            if rdata[0].value() in self.handlers:
                 self.handlers[rdata[0].value()](rdata[1:])
            else:
                self.error(11, "Unrecognized command")

    def reset_state(self):
        self.state.phase = "initial"
        self.state.remaining_time = self.state.time
        if self.state.rem and self.state.rem.running:
            self.state.rem.stop()
        if self.state.tick and self.state.tick.running:
            self.state.tick.stop()

    def connectionLost(self, reason):
        if self.name in self.users:
            del self.users[self.name]
            self.broadcast(cmd.disconnected, self.name)
            self.broadcast(cmd.reset)
            self.reset_state()

    def write(self, func, *args):
        self.transport.write(
            (func(*args) + '\r\n').encode('utf-8'))

    def error(self, code, message):
        self.write(cmd.error, code, message)

    def broadcast(self, func, *args):
        #FIXME refactor too many func(*args) calls
        self.log.info("BRCAST::"+func(*args))
        for user in self.users.values():
            GameProtocol.write(user, func, *args)

    def broadcast_rest(self, func, *args):
        for user in self.users.values():
            if self != user:
                GameProtocol.write(user, func, *args)

    def is_ready(self):
        return self.phase == "ready"

    def process_ready(self, data):
        self.phase = "ready"
        nplayers = self.state.number_players
        allrdy = all(map(GameProtocol.is_ready, self.users.values()))
        if allrdy and len(self.users) == nplayers and self.state.phase == "initial":
            self.state.phase = "ready"
            self.broadcast(cmd.ready)
            self.broadcast(cmd.total_time, self.state.time)
            self.broadcast(cmd.players, list(self.users.keys()))
            self.state.comparison_words = tuple(tuple(x.values()) for x in self.state.words)
            #print(self.state.comparison_words)
            w = tuple((x[2], x[1]) for x in self.state.comparison_words)
            self.broadcast(cmd.words, w)
            self.state.rem = LoopingCall(self.countdown)
            self.state.rem.start(1)
            self.state.tick = LoopingCall(
                lambda: self.broadcast(
                    cmd.tick,
                    self.state.remaining_time))
            self.state.tick.start(1)

    def countdown(self):
        timer = countdown_task(self.state)
        timer.addCallback(self.check_for_timeout)
        return timer.callback(None)

    def check_for_timeout(self, res):
        if self.state.phase == "timeout":
            self.broadcast(cmd.guesses, self.state.comparison_words)
            self.state.words = random.sample(self.state.total_words, 5)
            self.broadcast(cmd.reset)
            self.reset_state()
            reactor.callLater(4, self.process_ready, [])

    def process_guesses(self, data):
        results = equal_words(self.state.comparison_words, data[0])
        if all(results):
            self.broadcast(cmd.winner, self.name)
            self.broadcast(cmd.guesses, self.state.comparison_words)
            self.state.words = random.sample(self.state.total_words, 5)
            self.broadcast(cmd.reset)
            self.reset_state()
            reactor.callLater(4, self.process_ready, [])
        else:
            self.broadcast(cmd.correct, self.name, results)

    def process_errors(self, data):
        print('error received: {0}'.format(data))

class GameFactory(Factory):

    def __init__(self, number, tim, dwords, log=logging):
        data = read_whole_dict(dwords) #FIXME blocks
        total_words = process_dict(data)
        self.state = Bunch()
        self.state.total_words = total_words
        self.state.words = random.sample(total_words, 5)
        self.state.time = tim
        self.state.remaining_time = tim
        self.state.number_players = number
        self.state.phase = "initial"
        self.state.rem = None
        self.state.tick = None
        self.users = {}
        self.log = log

    def buildProtocol(self, addr):
        return GameProtocol(self.users, self.state, self.log)

if __name__ == '__main__':
    if len(argv) > 1:
        DICT = argv[1]
    else:    
        DICT = "words"
    reactor.listenTCP(9022, GameFactory(NUMBER_PLAYERS, TIME, DICT))
    reactor.run()
