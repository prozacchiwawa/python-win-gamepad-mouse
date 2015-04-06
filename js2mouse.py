import sys
import time
from pygame.locals import *
import pygame, pygame.joystick, pygame.event

pygame.init()

if not pygame.joystick.get_init():
    pygame.joystick_init()

class GamePadInput:
    def __init__(self):
        self.stick = None
        self.sticks = dict([(s.get_id(),s) for s in [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]])
        self.events = []
        self.hats = None
        self.axes = None
        self.buttons = None
        self.serial = 0

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

    def stream(self):
        if self.events is None:
            return None
        self.events = pygame.event.get()
        for event in self.events:
            self.serial += 1
            if event.type == QUIT:
                self.events = None
                break
            elif event.type == JOYAXISMOTION:
                self.refresh_axes()
            elif event.type == JOYBUTTONUP or event.type == JOYBUTTONDOWN:
                self.refresh_buttons()
            elif event.type == JOYHATMOTION:
                self.refresh_hats()
        self.events = []
        return {"serial":self.serial, "axes":self.axes, "buttons":self.buttons, "hats":self.hats}

class rate_limiter:
    def __init__(self,fun,pred,timings):
        self.fun = fun
        self.pred = pred
        self.timings = timings
        self.mode = 0
        self.last = None
        self.reset_remaining()

    def reset_remaining(self):
        self.remaining = self.timings[self.mode][0]
    
    def stream(self):
        sleeptime = self.timings[self.mode][1]
        print 'sleep',sleeptime
        time.sleep(sleeptime)
        event = self.fun()
        if self.last is None or self.pred(self.last,event):
            if self.remaining is not None:
                print 'remaining',self.remaining
                self.remaining -= 1
                if self.remaining == 0:
                    self.mode += 1
                    self.reset_remaining()
        else:
            self.mode = 0
            self.reset_remaining()
        self.last = event
        return event

job = GamePadInput()
if len(sys.argv) > 1:
    job.attach(int(sys.argv[1]))
    r = rate_limiter(job.stream,lambda x,y: x['serial'] == y['serial'],[(250,0.01),(250,0.1),(None,1)])
    for event in iter(r.stream, None):
        print event
else:
    print job.sticks
