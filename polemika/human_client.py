# -*- coding: utf-8 -*-
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol, task
from twisted.internet import fdesc, defer, error
import pygame
from datetime import datetime, date
import pygame,random,math
from pygame.locals import *
from random import randint
from datetime import time, tzinfo, timedelta
from copy import copy
from dummy_player import DummyAI, reset_state, write_on_connection
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.endpoints import connectProtocol
from mechanics import COMMANDS, cmd, GameProtocol, Bunch
from layout import create_layout
import random

from gui import draw_slot, draw_inputbox, draw_slot_text

def to_hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)

def convert_to_dict(words):
    res = []
    for word in words:
        if word[1] != "":
            p = prep_img(word[1])
        else:
            p = prep_img("pics/black.jpg")
        res.append({
            "word" :  word[0].decode("utf-8"),
            "pic"  :  p,
            "trans":  u"",
            "guess":  u"",})
    return res

class HumanPlayer(DummyAI):

    def process_words(self, data):
        global WORDS
        WORDS = convert_to_dict(data[0])
        self.state.words = WORDS
        self.state.block_input = False

    def process_tick(self, data):
        global remaining_time
        global progress_percent
        self.state.remaining_time = data[0]
        self.state.progress_percent = 100
        remaining_time = data[0]
        progress_percent = 100 #BAR_TICK * remaining_time

    def process_total_time(self, data):
        global TIME
        global BAR_TICK
        global progress_percent
        self.state.time = data[0]
        self.state.progress_percent = 100
        TIME = data[0]
        BAR_TICK = 100.0 / TIME
        progress_percent = 100

    def process_reset(self, data):
        global TIME
        global BAR_TICK
        global progress_percent
        global guesses
        DummyAI.process_reset(self, data)
        TIME = self.state.time
        BAR_TICK = 100.0 / TIME
        progress_percent = 100
        self.state.progress_percent = 100
        self.state.guesses = {k : [0,0,0,0,0] for k in guesses.keys()}
        guesses = {k : [0,0,0,0,0] for k in guesses.keys()}
        self.state.block_input = True

    def process_guesses(self, data):
        k = 0
        for entry in data[0]:
            WORDS[k]["trans"] = entry[0].decode("utf-8")
            self.state.words[k]["trans"] = entry[0].decode("utf-8")
            k += 1
        show_correct(WORDS)
        #show_correct(self.state.words)

    def process_correct(self, data):
        global guesses
        guesses[data[0]] = data[1]
        self.state.guesses[data[0]] = data[1]

    def process_players(self, data):
        global guesses
        guesses = {x : [0,0,0,0,0] for x in data[0]}
        self.state.guesses = {x : [0,0,0,0,0] for x in data[0]}

#constants
STDFONT = "/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-L.ttf"
PROGRESS_TEXT = "Time: {0}"
SELECTED = (128, 0, 100)
UNSELECTED = (128,128,128)
CORRECT_BOX = (0,10,255)
NOT_CORRECT_BOX = (255,10,0)
KANT_COLOR = (96, 96, 96)
DESIRED_FPS = 60.0
SCREEN_WIDTH, SCREEN_HEIGHT = (800,600)
DEFAULT_TABLE_COLOR = (50,50,50,80)
VICTORY_TABLE_COLOR=(0,180,0,80)
DEFEAT_TABLE_COLOR = (180,0,0,80)
time_total_seconds = lambda tm: tm.hour*60*60 + tm.minute*60 + tm.second
BAR_TICK = 0
TOTAL_PERCENT = 100
PROGRESS_STEP = float(TOTAL_PERCENT) / DESIRED_FPS



#global vars
surface, t_lb_surface = None, None
clock, small_font, font, big_font = None, None, None, None
progress_percent, guesses, TIME, remaining_time = None, None, None, None
layout = None

def init_pygame():
    global surface, t_lb_surface
    global clock, small_font, font, big_font, layout
    global progress_percent, guesses, TIME, remaining_time
    pygame.init()
    surface = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT),
                                      RESIZABLE)
    t_lb_surface = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT),
                                  pygame.SRCALPHA)
    t_lb_surface.fill(DEFAULT_TABLE_COLOR)
    pygame.display.set_caption("Fast memory game")
    clock = pygame.time.Clock()
    small_font = pygame.font.Font(STDFONT,14)
    font = pygame.font.Font(STDFONT,20)
    big_font = pygame.font.Font(STDFONT,24)
    progress_percent = 100
    guesses = {}
    TIME = -1
    remaining_time = -1
    layout = create_layout(surface, 10, 10)

prep_img = lambda x: pygame.image.load(x)

def draw_text(message,pos,color=(255,255,255)):
    surface.blit(font.render(message,1,color),pos)

def draw_progressbar(
        progress,
        coord,
        size=(148, 401),
        reverse=False,
        c1=(0, 128, 233),
        c2=(100,100,100)):
    """
    progress from 0 to 100.
    reversed direction 
    """
    total = size[0]
    progressw = int((total/100.0)*(100-progress))
    prog_w =  total - progressw if not reverse else progressw
    draw_slot(surface, coord, font, c2, size=size)
    draw_slot(surface, coord, font,
              c1, (prog_w, size[1]))


def draw_slots(words, selected_index, offset, margin, size):
    """[{"word":,"trans":,"pic":}..]"""
    multiplier=0
    lwords = len(words)
    size_y = round(size[1] / lwords) if lwords != 0 else 0
    slot_size = (size[0], size_y)
    for word in words:
        args = [
            surface,
            word["word"] + u"  • " + word["guess"],
            (offset[0],offset[1]+margin*multiplier),
            font,
            (100,100,100),
            (128,128,128),
            slot_size,
        ]
        if selected_index == multiplier:
            args.append(SELECTED)
        draw_inputbox(*args)
        multiplier += 1

def draw_player_correct_box(surface, value, coord, size):
    """Draw a correct box"""
    m = 2
    kant_box = pygame.Surface((size[0]+m, size[1]+m),pygame.SRCALPHA)
    box = pygame.Surface((size[0]-m, size[1]-m),pygame.SRCALPHA)
    kant_box.fill(KANT_COLOR)
    if value == 0:
        box.fill(NOT_CORRECT_BOX)
    elif value == 1:
        box.fill(CORRECT_BOX)
    else:
        raise ValueError("Correct box not 0/1")
    surface.blit(kant_box, coord)
    surface.blit(box, (coord[0]+m, coord[1]+m))
    

def draw_player_correct_bar(surface, correct, coord, size):
    """
    Draws CORRECT/NOT CORRECT labels for other players
    playing the game.
    """
    #draw_player_correct_box
    x, y = coord
    w, h = size
    off = 0
    box_w = 39.9 #why?
    for val in correct:
        draw_player_correct_box(surface, val, (x+off, y), (box_w, 10))
        off += box_w


def conv_guesses(guess):
    return " ".join([str(x) for x in guess])

def draw_player(coord, size, name, correct):
    name_h = round(size[1] * 0.5)
    guess_h = size[1] - name_h
    global font
    global small_font
    tmp = font
    font = small_font
    draw_slot_text(surface, name, coord, font, size=(200, name_h))
    draw_player_correct_bar(
        surface,
        correct,
        (coord[0], coord[1] + name_h),
        (200, name_h))
    font = tmp
    

def draw_players(players, coord):
    """[[name, [0, 0, 1, 0]], ...]"""
    x, y = coord
    h = 30
    for player in players.iteritems():
        draw_player((x, y), (150, h), player[0], player[1])
        y += h + 10

#horrible hacks/wrappers
def draw_grid_progress_left(s, pos, size):
    draw_progressbar(
        round(progress_percent),
        pos,
        c1=(100,100,100),
        c2=(0, 128, 233),
        reverse=False,
        size=size
    )

def draw_grid_progress_right(s, pos, size):
    draw_progressbar(
        round(progress_percent),
        pos,
        reverse=True,
        size=size
    )

def draw_grid_image(s, pos, size, state):
    surface.blit(
        pygame.transform.scale(
            WORDS[state.selected_index]['pic'], size),
        pos)

def draw_grid_words(s, pos, size, state):
    draw_slots(WORDS, state.selected_index, pos, 35, size)

def draw_grid_infobar(s, pos, size):
    draw_text(
        PROGRESS_TEXT.format(str(to_hms(remaining_time))),
        pos)

def draw_grid_players(s, pos, size):
    draw_players(
        guesses,
        pos)

def draw_grid_background(s, pos, size):
    s.blit(t_lb_surface,pos)

def draw_grid_fps_counter(s, pos, size):
    down = size[1]/2
    w,h = font.size("FPS:        ")
    draw_text("FPS: " + str(int(clock.get_fps())),
              (pos[0], pos[1]+down))

def draw_game(state):
    global layout
    global progress_percent
    layout.put(draw_grid_fps_counter, 0, 9, 1, 1)
    layout.put(draw_grid_background, 0, 0, 10, 10)
    layout.put(draw_grid_words, 1, 4, 8, 3, state)
    if len(WORDS) > 0:
        if WORDS[state.selected_index]['pic']:
            layout.put(draw_grid_image, 1, 0, 8, 4, state)
    layout.put(draw_grid_infobar, 1, 7, 8, 1)
    layout.put(draw_grid_players, 1, 8, 8, 2)
    layout.put(draw_grid_progress_left, 0, 0, 1, 7)
    layout.put(draw_grid_progress_right, 9, 0, 1, 7)

    if progress_percent >= PROGRESS_STEP:
        progress_percent -= PROGRESS_STEP

def game_tick(state):
    clock.tick(DESIRED_FPS)
    draw_game(state)
    pygame.display.flip()

#why polling? can't we use twisted for that?
def process_events(state, p):
    if state.block_input:
        return
    keys = pygame.key.get_pressed()
    if keys[pygame.K_BACKSPACE]:
        w = WORDS[state.selected_index]["guess"]
        WORDS[state.selected_index]["guess"] = w[:-1]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            reactor.stop()
        elif event.type == pygame.VIDEORESIZE:
            global surface, t_lb_surface
            surface = pygame.display.set_mode((event.w, event.h),
                                              RESIZABLE)
            t_lb_surface = pygame.Surface((event.w, event.h),
                                          pygame.SRCALPHA)
            t_lb_surface.fill(DEFAULT_TABLE_COLOR)
            layout.surface = surface
            layout.update()
        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_DOWN, pygame.K_TAB]:
                state.selected_index += 1
                if state.selected_index >= len(WORDS):
                    state.selected_index = 0
            elif event.key == pygame.K_UP:
                state.selected_index -= 1
                if state.selected_index < 0:
                    state.selected_index = len(WORDS) - 1
            elif event.key == pygame.K_RETURN:
                p.write(cmd.guesses, [x['guess'] for x in WORDS])
            else: #assume text input
                if len(WORDS) > 0:
                    WORDS[state.selected_index]["guess"] += event.unicode

def show_correct(words):
    for word in words:
        word["guess"] += u"  •  " + word["trans"]

def countdown_remaining_time():
    global remaining_time
    global rem
    global progress_percent
    #datetime.time can't do arithmetics, horrible code below
    if not remaining_time.hour and not remaining_time.minute and not remaining_time.second:
        t_lb_surface.fill(DEFEAT_TABLE_COLOR)
        rem.stop()
        task.deferLater(reactor, 2, reset_game)
        show_correct(WORDS)
        return
    td = date.today()
    remaining_time = datetime.combine(td, remaining_time) - datetime.combine(td, time(0, 0, 1))
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    remaining_time = time(hours, minutes, seconds)
    progress_percent -= BAR_TICK

def read_whole_dict(filename):
    with open(filename, "r") as f:
        data = [line for line in f.readlines()]
    return data

def process_line(line):
    raw = line[:-1].split(",")
    img = None
    if len(raw) == 3:
        img = prep_img(raw[2])
    return {
        "word" :  raw[1].decode("utf-8"),
        "pic"  :  img,
        "trans":  raw[0].decode("utf-8"),
        "guess":  u"",}

def process_dict(data):
    return [process_line(line) for line in data]

def reset_game():
    global rem
    global remaining_time
    global k
    global WORDS
    remaining_time = copy(TIME)
    k = 100
    rem.start(1)
    t_lb_surface.fill(DEFAULT_TABLE_COLOR)
    total_words = process_dict(data)
    WORDS = random.sample(total_words, 5)


WORDS = []
def start_game_loops(p, state):
    tick = LoopingCall(game_tick, state)
    tick.start(1.0 / DESIRED_FPS)

    ev = LoopingCall(process_events, state, p)
    ev.start(1.0 / 30)
    return p

def reset_human_client_state(state):
    state.progress_percent = 100
    state.selected_index = 0
    state.guesses = {}
    state.block_input = False
    return state

if __name__ == '__main__':
    init_pygame()
    point = TCP4ClientEndpoint(reactor, "localhost", 9022)
    state = Bunch()
    reset_state(state)
    reset_human_client_state(state)
    d = connectProtocol(point, HumanPlayer({}, state))
    d.addCallback(write_on_connection)
    d.addCallback(start_game_loops, state)
    reactor.run()
