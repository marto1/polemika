"""
GUI elements.
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
