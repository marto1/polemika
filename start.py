#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Game launcher.
By default it starts a single-player game with one bot.

* TODO redirect stdout/err for each node
* TODO Use the twisted app infrastructure
* TODO delegate to multiple processes
"""
import os
import sys
import logging
from sys import argv
from time import sleep
from twisted.internet import reactor, protocol, task
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.endpoints import connectProtocol
from polemika.mechanics import GameFactory, Bunch
from polemika.smarter_player import MomentAI
from polemika.human_client import HumanPlayer
from polemika.human_client import reset_human_client_state
from polemika.human_client import start_game_loops
from polemika.human_client import init_pygame
from polemika.dummy_player import reset_state, write_on_connection

def start_server(num_pl, time, dwords, fname):
    reactor.listenTCP(9022, GameFactory(num_pl, time, dwords))

def start_smart_player():
    point = TCP4ClientEndpoint(reactor, "localhost", 9022)
    state = Bunch()
    reset_state(state)
    d = connectProtocol(point, MomentAI({}, state))
    d.addCallback(write_on_connection)

def start_human_player():
    point = TCP4ClientEndpoint(reactor, "localhost", 9022)
    state = Bunch()
    reset_state(state)
    reset_human_client_state(state)
    d = connectProtocol(point, HumanPlayer({}, state))
    d.addCallback(write_on_connection)
    d.addCallback(start_game_loops, state)
    init_pygame()

if __name__ == '__main__':
    if len(argv) > 1:
        DICT = argv[1]
    else:    
        DICT = "words"
    start_server(2, 30, DICT, "server.log")
    sleep(1)
    start_smart_player()
    start_human_player()
    reactor.run()    
