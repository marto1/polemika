# -*- coding: utf-8 -*-
"""
GUI elements.

All reusable widgets end up here.
"""
import pygame

def render_text(surface, message, pos, font, color=(255,255,255)):
    return surface.blit(font.render(message,1,color),pos)

def draw_slot(
        surface,
        pos,
        size,
        font,
        color=(100,100,100)):
    """Draw a filled rectangle on the surface"""
    slot_surface = pygame.Surface(size, pygame.SRCALPHA)
    slot_surface.fill(color)
    return surface.blit(slot_surface, pos)

def draw_slot_text(
        surface,
        pos,
        size,
        message,
        font,
        color=(100,100,100)):
    """Draw a filled rectangle on the surface and add text"""
    draw_slot(surface, pos, size, font, color)
    return render_text(surface, message, pos, font)

def draw_inputbox(
        surface,
        pos,
        size,
        message,
        font,
        color=(100,100,100),
        incolor=(128,128,128),
        focused=False,
        thick=2):
    """Draw an editable slot(see draw_slot) with a label"""
    slot_cant = pygame.Surface(size, pygame.SRCALPHA)
    slot_cant.fill(incolor)
    surface.blit(slot_cant, pos)

    slot = pygame.Surface((size[0]-thick*2, size[1]-thick*2),
                          pygame.SRCALPHA)
    slot.fill(color)
    surface.blit(slot, (pos[0]+thick, pos[1]+thick))
    r = render_text(
        surface,
        message,
        (pos[0]+thick+2, pos[1]+thick+2),
        font)
    if focused:
        cursor = pygame.Surface((3, size[1]-thick*3), pygame.SRCALPHA)
        cursor.fill((48, 48, 48))
        surface.blit(cursor, r.topright)


def draw_progressbar(
        surface,
        pos,
        size,
        font,
        progress,
        reverse=False,
        c1=(0, 128, 233),
        c2=(100,100,100)):
    """
    A very simple progressbar made up from moving rects.
    progress from 0 to 100.
    reversed direction is optional(remember to flip colors also)
    """
    total = size[0]
    progressw = int((total/100.0)*(100-progress))
    prog_w =  total - progressw if not reverse else progressw
    draw_slot(surface, pos, size, font, c2)
    draw_slot(surface, pos, (prog_w, size[1]), font, c1)


def draw_slots(
        surface,
        pos,
        size,
        font,
        words,
        selected_index,
        margin,
        scolor):
    """[{"word":,"trans":,"pic":}..]"""
    multiplier=0
    lwords = len(words)
    size_y = round(size[1] / lwords) if lwords != 0 else 0
    slot_size = (size[0], size_y)
    for word in words:
        args = [
            surface,
            (pos[0],pos[1]+margin*multiplier),
            slot_size,
            word["word"] + u"  • " + word["guess"],
            font,
            (100,100,100),
            (128,128,128),
        ]
        if selected_index == multiplier:
            args.append(scolor)
        draw_inputbox(*args)
        multiplier += 1

