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
from functools import partial
from layout import create_layout
import random

from gui import draw_slot, draw_inputbox, draw_slot_text
from gui import draw_progressbar, draw_slots
from gui import draw_player_correct_bar, draw_players

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
    layout = create_layout(surface, 20, 20)

prep_img = lambda x: pygame.image.load(x)

def draw_text(message,pos,color=(255,255,255)):
    surface.blit(font.render(message,1,color),pos)    


def conv_guesses(guess):
    return " ".join([str(x) for x in guess])


#horrible hacks/wrappers
def draw_grid_image(s, pos, size, state):
    surface.blit(
        pygame.transform.scale(
            WORDS[state.selected_index]['pic'], size),
        pos)

def draw_grid_infobar(s, pos, size):
    draw_text(
        PROGRESS_TEXT.format(str(to_hms(remaining_time))),
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
    w_args = (font, WORDS, state.selected_index, 35, SELECTED)
    p = round(progress_percent)
    pr_args1 =  (font, p, False, (100,100,100), (0, 128, 233))
    pr_args2 =  (font, p, True)
    pl_args = (small_font, guesses)
    layout.put(draw_grid_background, 0, 0, 20, 20)
    layout.put(draw_grid_fps_counter, 0, 18, 1, 1)
    layout.put(draw_slots, 4, 11, 12, 7, *w_args)
    if len(WORDS) > 0: #at startup there are no words
        if WORDS[state.selected_index]['pic']:
            layout.put(draw_grid_image, 4, 1, 12, 10, state)
    layout.put(draw_grid_infobar, 0, 1, 4, 10)
    layout.put(draw_players, 16, 1, 4, 2, *pl_args)
    layout.put(draw_progressbar, 0, 0, 10, 1, *pr_args1)
    layout.put(draw_progressbar, 10, 0, 10, 1, *pr_args2)

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
