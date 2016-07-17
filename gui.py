"""
GUI elements.
"""

['__class__', '__coerce__', '__copy__', '__delattr__', '__delitem__', '__delslice__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getslice__', '__gt__', '__hash__', '__init__', '__le__', '__len__', '__lt__', '__ne__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__safe_for_unpickling__', '__setattr__', '__setitem__', '__setslice__', '__sizeof__', '__str__', '__subclasshook__', 'bottom', 'bottomleft', 'bottomright', 'center', 'centerx', 'centery', 'clamp', 'clamp_ip', 'clip', 'collidedict', 'collidedictall', 'collidelist', 'collidelistall', 'collidepoint', 'colliderect', 'contains', 'copy', 'fit', 'h', 'height', 'inflate', 'inflate_ip', 'left', 'midbottom', 'midleft', 'midright', 'midtop', 'move', 'move_ip', 'normalize', 'right', 'size', 'top', 'topleft', 'topright', 'union', 'union_ip', 'unionall', 'unionall_ip', 'w', 'width', 'x', 'y']

import pygame

def render_text(surface, message, pos, font, color=(255,255,255)):
    return surface.blit(font.render(message,1,color),pos)

def draw_slot(
        surface,
        pos,
        font,
        color=(100,100,100),
        size=(500, 21)):
    slot_surface = pygame.Surface(size, pygame.SRCALPHA)
    slot_surface.fill(color)
    return surface.blit(slot_surface, pos)

def draw_slot_text(
        surface,
        message,
        pos,
        font,
        color=(100,100,100),
        size=(500, 21)):
    draw_slot(surface, pos, font, color, size)
    return render_text(surface, message, pos, font)

def draw_inputbox(
        surface,
        message,
        pos,
        font,
        color=(100,100,100),
        incolor=(128,128,128),
        size=(500, 36),
        focused=False,
        thick=3):
    slot_cant = pygame.Surface(size, pygame.SRCALPHA)
    slot_cant.fill(incolor)
    surface.blit(slot_cant, pos)

    slot = pygame.Surface((size[0]-thick*2,size[1]-thick*2),
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
