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
import random
from mechanics import COMMANDS, cmd, GameProtocol, Bunch

class DummyAI(GameProtocol):

    letter_pool=u'abcdefghijklmnopqrstuvwxyzøåæ'
    longest_word = 9

    def choose_word(self, word):
        lw = self.longest_word
        lp = self.letter_pool
        n = random.randint(1, lw)
        res = ''.join(random.choice(lp) for _ in xrange(n))
        return res

    def process_ready(self, data):
        print("server is ready!")

    def process_players(self, data):
        self.state.players = data[0]

    def process_tick(self, data):
        self.state.remaining_time = data[0]

    def process_words(self, data):
        self.state.words = data[0]
        self.state.guess = LoopingCall(self.make_guesses)
        self.state.guess.start(0.5)

    def process_total_time(self, data):
        self.state.time = data[0]

    def process_ready(self, data):
        self.state.phase = "game"

    def process_winner(self, data):
        pass

    def process_reset(self, data):
        self.state.phase = "initial"
        self.state.guess.stop()

    def make_guesses(self):
        if self.state.remaining_time == 0: return
        if self.state.phase == "over": return
        self.write(cmd.guesses, self.translate())

    def translate(self):
        l = lambda x: self.choose_word(x)
        res = [l(w) for w in self.state.words]
        return res
        

def write_on_connection(p):
    p.write(cmd.ready)


def reset_state(state):
    state.phase = "initial"
    state.rem = None
    state.tick = None
    state.guess = None
    state.time = -1
    state.remaining_time = -1

if __name__ == '__main__':
    point = TCP4ClientEndpoint(reactor, "localhost", 9022)
    state = Bunch()
    reset_state(state)
    d = connectProtocol(point, DummyAI({}, state))
    d.addCallback(write_on_connection)
    reactor.run()

