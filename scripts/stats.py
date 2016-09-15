from sys import argv
from sexpdata import loads, dumps, Symbol

class Message(object):
    timestamp = None
    verb = None
    content = None

def get_message(line):
    m = Message()
    sp = line.split("::")
    m.timestamp = sp[0]
    m.verb = sp[1]
    m.content = loads(sp[2])
    return m

players = {}

def get_players(m):
    c = m.content
    if c[0].value() == "players":
        for player in c[1]:
            if player not in players:
                players[player] = {
                    'wins':0,
                    'accuracy':0.0,
                    'c':0.0,
                    't':0.0}

def get_wins(m):
    c = m.content
    if c[0].value() == "winner":
        if c[1] in players:
            players[c[1]]['wins'] += 1

def get_correct(m):
    c = m.content
    if c[0].value() == "correct":
        if c[1] in players:
            for guess in c[2]:
                if guess == 1:
                    players[c[1]]['c'] += 1
                players[c[1]]['t'] += 1

def get_correct_ratio():
    for name in players.keys():
        p = players[name]
        p['accuracy'] = (100 *p['c']) / p['t']

def process_message(m):
    get_players(m)
    get_wins(m)
    get_correct(m)
    
def main(filename):
    lines = open(filename,'r').readlines()
    lines = [get_message(x) for x in lines]
    for x in lines: process_message(x)
    get_correct_ratio()
    print players

if __name__ == '__main__':
    main(argv[1])
        

