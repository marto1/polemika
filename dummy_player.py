# -*- coding: utf-8 -*-
from __future__ import print_function
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol, task
from twisted.protocols.basic import LineReceiver
from twisted.internet import fdesc, defer, error
from twisted.internet.endpoints import TCP4ServerEndpoint
from datetime import datetime, date
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from mechanics import COMMANDS, cmd, GameProtocol, Bunch


class DummyAI(GameProtocol):

    def process_ready(self, data):
        print("server is ready!")

def write_on_connection(p):
    p.write(cmd.ready)
    # p.sendMessage("Hello")
    # reactor.callLater(1, p.sendMessage, "This is sent in a second")
    # reactor.callLater(2, p.transport.loseConnection)

if __name__ == '__main__':
    point = TCP4ClientEndpoint(reactor, "localhost", 9022)
    state = Bunch()
    state.phase = "initial"
    state.rem = None
    state.tick = None
    state.time = -1
    state.remaining_time = -1
    d = connectProtocol(point, DummyAI({}, state))
    d.addCallback(write_on_connection)
    reactor.run()

