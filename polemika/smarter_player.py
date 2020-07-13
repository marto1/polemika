"""
AI begins without words.
Will remember some words depending on frequency of occurrence.
The rest will be dummy guessed.
"""

from polemika.dummy_player import *
from polemika.mechanics import COMMANDS, cmd, Bunch
from random import randint, choice

class MomentAI(DummyAI):

    direct_pool = {}
    blurry_pool = {}
    max_direct = 10
    max_blurry = 50
    chance_blurry = 65 #1-100; 100 always
    transfer_tresh = 3 #transfer to direct pool on treshhold

    def remember(self, word):
        if self.blurry_pool[word]["trans"] == "":
            return ""
        chance = randint(1, 100)
        if chance < self.chance_blurry:
            return self.blurry_pool[word]["trans"]
        else:
            return DummyAI.choose_word(self, word)

    def add_to_blurry(self, word):
        if len(self.blurry_pool) >= self.max_blurry:
            ch = choice(list(self.blurry_pool.keys()))
            del self.blurry_pool[ch]
        self.blurry_pool[word] = {"trans": "", "count": 0}    

    def choose_word(self, word):
        w = word[0]
        if w in self.direct_pool:
            return self.direct_pool[w]
        if w in self.blurry_pool:
            rem = self.remember(w)
            if rem != '':
                return rem
        else:
            self.add_to_blurry(w)
        return DummyAI.choose_word(self, w)

    def process_guesses(self, data):
        k = 0
        for entry in data[0]:
            word = self.state.words[k][0]
            if word in self.blurry_pool:
                if self.blurry_pool[word]["count"] >= self.transfer_tresh:
                    if len(self.direct_pool) >= self.max_direct:
                        ch = choice(list(self.direct_pool.keys()))
                        del self.direct_pool[ch]
                    self.direct_pool[word] = entry[0]
                    del self.blurry_pool[word]
                    continue
                self.blurry_pool[word]["trans"] = entry[0]
                self.blurry_pool[word]["count"] += 1
            k += 1
            
    
if __name__ == '__main__':
    point = TCP4ClientEndpoint(reactor, "localhost", 9022)
    state = Bunch()
    reset_state(state)
    d = connectProtocol(point, MomentAI({}, state))
    d.addCallback(write_on_connection)
    reactor.run()
