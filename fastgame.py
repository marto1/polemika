# -*- coding: utf-8 -*-
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol, task
from twisted.internet import fdesc, defer, error
import pygame
from datetime import datetime, date

import pygame,random,math
from pygame.locals import *
from math import fabs
from random import randint
from datetime import time, tzinfo, timedelta
from copy import copy
import random

#TODO refactor

#constants
STDFONT = "/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-L.ttf"
PROGRESS_TEXT = " "*60+"Time: {0}"
SELECTED = (128, 0, 100)
UNSELECTED = (128,128,128)
DESIRED_FPS = 60.0
TIME = time(0, 1, 0)
SCREEN_WIDTH, SCREEN_HEIGHT = (800,600)
DEFAULT_TABLE_COLOR = (50,50,50,80)
VICTORY_TABLE_COLOR=(0,180,0,80)
DEFEAT_TABLE_COLOR = (180,0,0,80)
time_total_seconds = lambda tm: tm.hour*60*60 + tm.minute*60 + tm.second
BAR_TICK = 100.0 / time_total_seconds(TIME)

pygame.init()

#global vars
surface = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
t_surface = pygame.Surface((SCREEN_WIDTH,25),pygame.SRCALPHA)
t_lb_surface = pygame.Surface((SCREEN_WIDTH,400),pygame.SRCALPHA)
t_surface.fill(DEFAULT_TABLE_COLOR)
t_lb_surface.fill(DEFAULT_TABLE_COLOR)
pygame.display.set_caption("Fast memory game")
clock = pygame.time.Clock()
font = pygame.font.Font(STDFONT,20)
big_font = pygame.font.Font(STDFONT,24)
progress_percent = 100
remaining_time = copy(TIME)
selected_index = 0


prep_img = lambda x: pygame.transform.scale(
    pygame.image.load(x),
    (250, 150))

def drawText(message,pos,color=(255,255,255)):
    surface.blit(font.render(message,1,color),pos)

def drawSlot(message, pos, color=(128,128,128), size=(500, 21)):
    slot_surface = pygame.Surface(size, pygame.SRCALPHA)
    slot_surface.fill(color)
    surface.blit(slot_surface, pos)
    drawText(message, pos)

def drawProgressBar(message, progress):
    """progress from 0 to 100"""
    total = SCREEN_WIDTH-50
    progressw = int((total/100.0)*(100-progress))
    drawSlot("", (20, 420), size=(total, 70))
    drawSlot(message, (20, 420), (0, 128, 233), (total-progressw, 70))


def draw_slots(words, selected_index, offset, margin):
    """[{"word":,"trans":,"pic":}..]"""
    multiplier=1
    for word in words:
        args = [
            word["word"] + "   " + word["guess"],
            (offset[0],offset[1]+margin*multiplier)]
        if selected_index == (multiplier-1):
            args.append(SELECTED)
        drawSlot(*args)
        multiplier += 1

def draw_game():
    global progress_percent
    global remaining_time
    global selected_index
    w,h = font.size("FPS:        ")
    margin = 35
    surface.blit(pygame.transform.scale(t_surface,(w,h)),
                 (8,SCREEN_HEIGHT-30))
    surface.blit(t_lb_surface,(0,0))
    drawText("FPS: " + str(int(clock.get_fps())),(10,SCREEN_HEIGHT-30))
    surface.blit(big_font.render("Guess words",0,
                                 (255,255,255)),(SCREEN_WIDTH/2.5,20))
    draw_slots(WORDS, selected_index, (30,20), 35)
    if WORDS[selected_index]['pic']:
        surface.blit(
            WORDS[selected_index]['pic'],
            (SCREEN_WIDTH-260, 20+margin))

    drawProgressBar(
        PROGRESS_TEXT.format(str(remaining_time)),
        round(progress_percent))
    #TODO make progress bar smooth

def game_tick():
    clock.tick(DESIRED_FPS)
    draw_game()
    pygame.display.flip()

def check_success(words):
    for word in words:
        if word["guess"] != word["trans"]:
            return False
    return True

def process_events(): #why polling? can't we use twisted for that?
    global selected_index
    keys = pygame.key.get_pressed()
    if keys[pygame.K_BACKSPACE]:
        w = WORDS[selected_index]["guess"]
        WORDS[selected_index]["guess"] = w[:-1]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            reactor.stop() # just stop somehow
        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_DOWN, pygame.K_TAB]:
                selected_index += 1
                if selected_index >= len(WORDS):
                    selected_index = 0
            elif event.key == pygame.K_UP:
                selected_index -= 1
                if selected_index < 0:
                    selected_index = len(WORDS) - 1
            elif event.key == pygame.K_RETURN:
                issuccess = check_success(WORDS)
                if issuccess == True:
                    t_lb_surface.fill(VICTORY_TABLE_COLOR)
                    global rem
                    rem.stop()
                    task.deferLater(reactor, 2, reset_game)
            else: #assume text input
                WORDS[selected_index]["guess"] += event.unicode

def show_correct(words):
    for word in words:
        word["guess"] += " " + word["trans"]

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


data = read_whole_dict("words")
total_words = process_dict(data)
WORDS = random.sample(total_words, 5)

tick = LoopingCall(game_tick)
tick.start(1.0 / DESIRED_FPS)

ev = LoopingCall(process_events)
ev.start(1.0 / 30)

rem = LoopingCall(countdown_remaining_time)
rem.start(1)

reactor.run()
