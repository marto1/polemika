#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Game launcher.
By default it starts a single-player game with one bot.

"""
from twisted.internet import reactor, protocol, task
from multiprocessing import Process #should be done with this
from os import system
from sys import argv
from polemika.mechanics import GameFactory

def start_server():
    reactor.listenTCP(9022, GameFactory())
    reactor.run()

def start_smart_player():
    pass

if __name__ == '__main__':
    if len(argv) > 1:
        DICT = argv[1]
    else:    
        DICT = "words"
    p = Process(target=start_server, args=())
    p.start()
