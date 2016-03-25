#!/usr/bin/env python3
from random import choice as c
from sys import argv
from time import sleep,time
from functools import partial
from twisted.internet import defer
import json

def one_to_many_arg(fn):
    def wrapped(*args):
        return fn(*args[0])
    return wrapped


#Game logic.
def play_random_choice(words):
    answer, word = c(words)[:-1].split(",")
    result = input("{0} : ".format(word))
    return result, answer

def print_and_wait(delay, message):
    print(message)
    sleep(delay)

@one_to_many_arg
def react_choice(res, true_delay, true_message, false_delay, false_message):
    if res: print_and_wait(true_delay, true_message)
    else: print_and_wait(false_delay, false_message)
    return True

@one_to_many_arg
def prepare_react(result, answer, time):
    tmess = "correct.;T:{0}".format(time)
    fmess = "no, {0} ;T:{1}".format(answer, time)
    return result == answer, 0.5, tmess, 2, fmess

def start_measuring(words):
    start = time()
    return words, start

@one_to_many_arg
def stop_measuring(result, answer, start):
    t = round(time() - start, 3)
    return result, answer, t

@one_to_many_arg
def play_and_pass_time(words, start):
    r = play_random_choice(words)
    return r[0], r[1], start

def pass_exception(e):
    return e

def keyboard_interrupt(e):
    e.trap(KeyboardInterrupt)
    import os #FUCK
    os._exit(1)
    
def prepare_game(game_chain):
    game_chain.addCallback(start_measuring)
    game_chain.addCallbacks(play_and_pass_time, pass_exception)
    game_chain.addCallbacks(stop_measuring, pass_exception)
    game_chain.addCallbacks(prepare_react, pass_exception)
    game_chain.addCallbacks(react_choice, keyboard_interrupt)
    return game_chain

def after_play_hook(data, result):
    save_result_from_game(f, result)

def after_react_hook(data, cmpr, sdelay, smess, fdelay, fmess):
    pass

#statistic functions
def save_result_from_game(f, result):
    f.write(json.dumps(result))


def play(words):
    game_state = defer.Deferred()
    prepare_game(game_state)
    return game_state.callback(words)
    

#main function
def main():
    with open(argv[1], "r") as f:
        data = [line for line in f.readlines()]
    with open(argv[2], "w") as f:
        results = {}
        aftp = partial(after_play_hook, results)
        aftr = partial(after_react_hook, results)
        while True:
            print("\x1b[2J\x1b[H")
            play(data)

if __name__ == '__main__':
    main()
