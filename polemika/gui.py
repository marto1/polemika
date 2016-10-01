# -*- coding: utf-8 -*-
"""
GUI elements.

All reusable widgets end up here.
"""
import pygame

CORRECT_BOX = (0, 10, 255)
NOT_CORRECT_BOX = (255, 10, 0)
KANT_COLOR = (96, 96, 96)


def render_text(surface, message, pos, font, color=(255, 255, 255)):
    return surface.blit(font.render(message, 1, color), pos)


def draw_slot(
        surface,
        pos,
        size,
        font,
        color=(100, 100, 100)):
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
        color=(100, 100, 100)):
    """Draw a filled rectangle on the surface and add text"""
    draw_slot(surface, pos, size, font, color)
    return render_text(surface, message, pos, font)


def draw_inputbox(
        surface,
        pos,
        size,
        message,
        font,
        color=(100, 100, 100),
        incolor=(128, 128, 128),
        focused=False,
        thick=2):
    """Draw an editable slot(see draw_slot) with a label"""
    slot_cant = pygame.Surface(size, pygame.SRCALPHA)
    slot_cant.fill(incolor)
    surface.blit(slot_cant, pos)

    slot = pygame.Surface((size[0]-thick*2, size[1]-thick*2),
                          pygame.SRCALPHA)
    slot.fill(color)
    ys = (pos[1]+thick)
    surface.blit(slot, (pos[0]+thick, ys))
    r = render_text(
        surface,
        message,
        (pos[0]+thick+2, ys),
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
        c2=(100, 100, 100)):
    """
    A very simple progressbar made up from moving rects.
    progress from 0 to 100.
    reversed direction is optional(remember to flip colors also)
    """
    total = size[0]
    progressw = int((total/100.0)*(100-progress))
    prog_w = total - progressw if not reverse else progressw
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
    multiplier = 0
    lwords = len(words)
    size_y = size[1] / lwords if lwords != 0 else 0
    slot_size = (size[0], size_y)
    for word in words:
        args = [
            surface,
            (pos[0], pos[1]+size_y*multiplier+margin),
            slot_size,
            word["word"] + u"  • " + word["guess"],
            font,
            (100, 100, 100),
            (128, 128, 128),
        ]
        if selected_index == multiplier:
            args.append(scolor)
        draw_inputbox(*args)
        multiplier += 1


def draw_player_correct_box(
        surface,
        pos,
        size,
        value):
    """Draw a correct box"""
    m = 2
    kant_box = pygame.Surface((size[0]+m, size[1]+m), pygame.SRCALPHA)
    box = pygame.Surface((size[0]-m, size[1]-m), pygame.SRCALPHA)
    kant_box.fill(KANT_COLOR)
    if value == 0:
        box.fill(NOT_CORRECT_BOX)
    elif value == 1:
        box.fill(CORRECT_BOX)
    else:
        raise ValueError("Correct box not 0/1")
    surface.blit(kant_box, pos)
    surface.blit(box, (pos[0]+m, pos[1]+m))


def draw_player_correct_bar(
        surface,
        pos,
        size,
        correct):
    """
    Draws CORRECT/NOT CORRECT labels for other players
    playing the game.
    """
    x, y = pos
    w, h = size
    off = 0
    lcorr = len(correct)
    box_w = size[0] / lcorr if lcorr > 0 else 0
    for val in correct:
        draw_player_correct_box(surface, (x+off, y), (box_w, 10), val)
        off += box_w


def draw_player(
        surface,
        pos,
        size,
        font,
        name,
        correct):
    name_h = round(size[1] * 0.5)
    draw_slot_text(surface, pos, (size[0], name_h), name, font)
    draw_player_correct_bar(
        surface,
        (pos[0], pos[1] + name_h),
        (size[0], name_h),
        correct)


def draw_players(
        surface,
        pos,
        size,
        font,
        players):
    """[[name, [0, 0, 1, 0]], ...]"""
    x, y = pos
    h = 30
    for player in players.iteritems():
        draw_player(
            surface,
            (x, y),
            (size[0], h),
            font,
            player[0],
            player[1])
        y += h + 10
