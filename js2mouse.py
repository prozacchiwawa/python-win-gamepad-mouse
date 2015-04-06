import sys
from pygame.locals import *
import pygame, pygame.joystick, pygame.event

pygame.init()

if not pygame.joystick.get_init():
    pygame.joystick_init()

class GamePadInput:
    def __init__(self):
        self.stick = None
        self.sticks = dict([(s.get_id(),s) for s in [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]])
        self.hats = None
        self.axes = None
        self.buttons = None

    def attach(self,sid):
        self.stick = self.sticks[sid]
        self.stick.init()
        self.refresh_axes()
        self.refresh_hats()
        self.refresh_buttons()

    def refresh_axes(self):
        self.axes = [self.stick.get_axis(x) for x in range(self.stick.get_numaxes())]

    def refresh_hats(self):
        self.hats = [self.stick.get_hat(x) for x in range(self.stick.get_numhats())]

    def refresh_buttons(self):
        self.buttons = [self.stick.get_button(x) for x in range(self.stick.get_numbuttons())]

    def run(self):
        while True:
            for event in pygame.event.get():
                print 'event',event.type
                if event.type == QUIT:
                    print 'quit event'
                    return
                elif event.type == JOYAXISMOTION:
                    self.refresh_axes()
                    print 'axes',self.axes
                elif event.type == JOYBUTTONUP or event.type == JOYBUTTONDOWN:
                    self.refresh_buttons()
                    print 'buttons',self.buttons
                elif event.type == JOYHATMOTION:
                    self.refresh_hats()
                    print 'hats',self.hats
    
job = GamePadInput()
if len(sys.argv) > 1:
    job.attach(int(sys.argv[1]))
    job.run()
else:
    print job.sticks
