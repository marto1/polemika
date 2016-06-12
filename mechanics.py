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

def read_whole_dict(filename):
    with open(filename, "r") as f:
        data = [line for line in f.readlines()]
    return data

def process_line(line):
    raw = line[:-1].split(",")
    img = None
    if len(raw) == 3:
        img = raw[2]
    return {
        "word" :  raw[1].decode("utf-8"),
        "pic"  :  img,
        "trans":  raw[0].decode("utf-8"),}

def process_dict(data):
    return [process_line(line) for line in data]

data = read_whole_dict("words")
total_words = process_dict(data)
words = random.sample(total_words, 5)
TIME = 4200 #seconds
remaining_time = TIME

def countdown_remaining_time(x=None):
    global remaining_time
    if remaining_time == 0: return False
    remaining_time -= 1
    return True

def reset_game(remaining_time): 
    remaining_time = TIME
    rem.start(1)
    total_words = process_dict(data) #FIXME why
    words = random.sample(total_words, 5)
    return words


def countdown_task():
    res = defer.Deferred()
    res.addCallback(countdown_remaining_time)
    res.addCallback(lambda x: print(x))
    return res

rstr = lambda N: ''.join(random.choice(
    string.ascii_uppercase + string.digits) for _ in range(N))

class GameProtocol(LineReceiver):

    def __init__(self, users):
        self.users = users
        self.name = rstr(20)
        self.users[self.name] = self
        
    def lineReceived(self, line):
        return 

    def connectionLost(self, reason):
        if self.users.has_key(self.name):
            del self.users[self.name]

class GameFactory(Factory):

    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        return GameProtocol(self.users)

if __name__ == '__main__':    
    rem = LoopingCall(lambda: countdown_task().callback(None))
    rem.start(1)
    
    reactor.listenTCP(9022, GameFactory())

    reactor.run()
