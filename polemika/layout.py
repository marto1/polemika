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
        self.update()

    def get_position(self, xtile, ytile, xspan=1, yspan=1):
        """Calculates absolute coordinates and size."""
        xstep, ystep = self.xstep, self.ystep
        return (
            self.surface,
            (xstep*xtile, ytile*ystep),
            (xstep*xspan, ystep*yspan))

    def put(self, draw, xtile, ytile, xspan=1, yspan=1, *args):
        """Calculates layout and draws on screen. Careful."""
        gpos = self.get_position
        res = gpos(xtile, ytile, xspan, yspan)+args
        return draw(*res)

    def update(self):
        self.xstep = self.surface.get_width() / self.cols
        self.ystep = self.surface.get_height() / self.rows

def create_layout(surface, cols, rows):
    return Layout(surface, cols, rows)

