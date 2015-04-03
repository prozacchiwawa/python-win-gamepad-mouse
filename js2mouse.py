import sys
from pygame.locals import *
import pygame, pygame.joystick, pygame.event

pygame.init()

if not pygame.joystick.get_init():
    pygame.joystick_init()

stick = None
sticks = dict([(s.get_id(),s) for s in [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]])
if len(sys.argv) > 1:
    stick = sticks[int(sys.argv[1])]
    print stick
    stick.init()
else:
    print sticks
    sys.exit(0)

axes = [0 for x in range(stick.get_numaxes())]
buttons = [False for x in range(stick.get_numbuttons())]
hats = [0 for x in range(stick.get_numhats())]

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit(0)
        elif event.type == JOYAXISMOTION:
            axes = [stick.get_axis(x) for x in range(stick.get_numaxes())]
            print 'axes',axes
        elif event.type == JOYBUTTONUP or event.type == JOYBUTTONDOWN:
            buttons = [stick.get_button(x) for x in range(stick.get_numbuttons())]
            print 'buttons',buttons
        elif event.type == JOYHATMOTION:
            hats = [stick.get_hat(x) for x in range(stick.get_numhats())]
            print 'hats',hats
    
