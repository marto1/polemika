#!/usr/bin/env python3
from random import choice as c
from sys import argv
from time import sleep,time
from functools import partial
from twisted.internet import defer
import json

def passit(*args, **kwargs):
    pass

#Should have only game logic.
#Every function should provide hooks
#for logging, etc.
#Maybe refactor with deferreds
def play_random_choice(words):
    answer, word = c(words)[:-1].split(",")
    result = input("{0} : ".format(word))
    return result, answer

def print_and_wait(delay, message):
    print(message)
    sleep(delay)

def react_choice(res, true_delay, true_message, false_delay, false_message):
    if res: print_and_wait(true_delay, true_message)
    else: print_and_wait(false_delay, false_message)

def play_game(words, stats, after_play=passit, after_react=passit):
    start = time()
    r = play_random_choice(words)
    t = round(time() - start, 3)
    r.append(t)
    after_play(r)
    tmess = "correct.;T:{0}".format(t)
    fmess = "no, {0} ;T:{1}".format(r[1], t)
    dargs = r[0] == r[1], 0.5, tmess, 2, fmess
    react_choice(*dargs)
    after_react(*dargs)

#statistic functions
def save_result_from_game(f, result):
    f.write(json.dumps(result))

#main function
def main():
    def after_play_hook(data, result):
        save_result_from_game(f, result)

    def after_react_hook(data, cmpr, sdelay, smess, fdelay, fmess):
        pass

    with open(argv[1], "r") as f:
        data = [line for line in f.readlines()]
    with open(argv[2], "w") as f:
        results = {}
        aftp = partial(after_play_hook, results)
        aftr = partial(after_react_hook, results)
        while True:
            print("\x1b[2J\x1b[H")
            play_game(data, f, aftp, aftr)
            

if __name__ == '__main__':
    main()
