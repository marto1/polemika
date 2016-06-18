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
import string

NUMBER_PLAYERS = 2
TIME = 4200 #seconds

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
    y : partial(dump_command, z) for y,z in COMMANDS.iteritems()
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
    return {
        "word" :  raw[1].decode("utf-8"),
        "pic"  :  img,
        "trans":  raw[0].decode("utf-8"),}

def process_dict(data):
    return [process_line(line) for line in data]


def countdown_remaining_time(x=None, state=None):
    if state.remaining_time == 0: return -1
    state.remaining_time -= 1
    return state.remaining_time

def reset_game(x=None, state=None):
    print(x)
    # remaining_time = TIME
    # rem.start(1)
    # total_words = process_dict(data) #FIXME why
    # words = random.sample(total_words, 5)
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
        print(words[k][0], end=" ")
        print(guess)
        if words[k][0] == guess:
            res.append(1)
        else:
            res.append(0)
        k += 1
    return res

class GameProtocol(LineReceiver):

    def process_tick(self, data): pass
    def process_players(self, data): pass
    def process_words(self, data): pass
    def process_total_time(self, data): pass

    def __init__(self, users, state):
        self.state = state
        self.users = users
        self.name = rstr(20)
        self.users[self.name] = self
        self.phase = "initial"
        #FIXME map with COMMANDS
        self.handlers = {
            'ready': self.process_ready,
            'guesses': self.process_guesses,
            'error' : self.process_errors,
            'players' : self.process_players,
            'words' : self.process_words,
            'tick' : self.process_tick,
            'total_time' : self.process_total_time,
        }

    def lineReceived(self, line):
        print("RAW:" + line)
        try:
            rdata = loads(line)
        except Exception:
            self.error(10, "Invalid syntax")
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

    def connectionLost(self, reason):
        if self.users.has_key(self.name):
            del self.users[self.name]
            self.broadcast(cmd.disconnected, self.name)
            self.state.phase = "initial"
            if self.state.rem and self.state.rem.running:
                self.state.rem.stop()
            if self.state.tick and self.state.tick.running:
                self.state.tick.stop()
            self.state.remaining_time = self.state.time

    def write(self, func, *args):
        self.transport.write(
            (func(*args) + '\r\n').encode('utf-8'))

    def error(self, code, message):
        self.write(cmd.error, code, message)

    def broadcast(self, func, *args):
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
            self.broadcast(cmd.players, self.users.keys())
            self.state.comparison_words = tuple(tuple(x.values()) for x in self.state.words)
            print(self.state.comparison_words)
            w = tuple((x[2], x[1]) for x in self.state.comparison_words)
            self.broadcast(cmd.words, w)
            t = lambda x: countdown_task(x).callback(None)
            self.state.rem = LoopingCall(t, self.state)
            self.state.rem.start(1)
            self.state.tick = LoopingCall(
                lambda: self.broadcast(
                    cmd.tick,
                    self.state.remaining_time))
            self.state.tick.start(3)

    def process_guesses(self, data):
        results = equal_words(self.state.comparison_words, data[0])
        if all(results):
            self.broadcast(cmd.winner, self.name)
        else:
            self.broadcast_rest(cmd.correct, self.name, results)

    def process_errors(self, data):
        print('error received: {0}'.format(data))


class GameFactory(Factory):

    def __init__(self):
        data = read_whole_dict("words") #FIXME blocks
        total_words = process_dict(data)
        self.state = Bunch()
        self.state.total_words = total_words
        self.state.words = random.sample(total_words, 5)
        self.state.time = TIME
        self.state.remaining_time = TIME
        self.state.number_players = NUMBER_PLAYERS
        self.state.phase = "initial"
        self.state.rem = None
        self.state.tick = None
        self.users = {}

    def buildProtocol(self, addr):
        return GameProtocol(self.users, self.state)

if __name__ == '__main__':
    reactor.listenTCP(9022, GameFactory())
    reactor.run()
