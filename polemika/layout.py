# -*- coding: utf-8 -*-
"""
A non-intrusive grid layout for pygame.
https://github.com/marto1/pygamegrid
"""
import pygame
from pygame.locals import *

class Layout(object):

    def __init__(self, surface, cols, rows):
        self.surface = surface
        self.cols = cols
        self.rows = rows
        self.xstep = surface.get_width() / cols
        self.ystep = surface.get_height() / rows

    def put(self, draw, xtile, ytile, xspan=1, yspan=1, args=()):
        xstep, ystep = self.xstep, self.ystep
        return draw(
            self.surface,
            (xstep*xtile, ytile*ystep),
            (xstep*xspan, ystep*yspan))

def create_layout(surface, cols, rows):
    return Layout(surface, cols, rows)

