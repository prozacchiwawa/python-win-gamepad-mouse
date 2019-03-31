import sys
import time
import json
import uinput
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
        self.hats = sum([list(self.stick.get_hat(x)) for x in range(self.stick.get_numhats())], [])

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
    def __init__(self,pred,timings,instream):
        self.instream = instream
        self.pred = pred
        self.timings = timings
        self.mode = 0
        self.last = None
        self.reset_remaining()

    def reset_remaining(self):
        self.remaining = self.timings[self.mode][0]
    
    def stream(self):
        sleeptime = self.timings[self.mode][1]
        time.sleep(sleeptime)
        event = self.instream.stream()
        if self.last is None or self.pred(self.last,event):
            if self.remaining is not None:
                self.remaining -= 1
                if self.remaining == 0:
                    self.mode += 1
                    self.reset_remaining()
        else:
            self.mode = 0
            self.reset_remaining()
        self.last = event
        return event

class TranslateMouse:
    def __init__(self,settings,instream):
        self.settings = settings
        self.instream = instream
        self.prev = { }

    def get_val(self,key,event,setting_row):
        elabel, eindex = setting_row[:2]
        scale = setting_row[2] if len(setting_row) >= 3 else 1.0
        offset = setting_row[3] if len(setting_row) >= 4 else 0.0
        raw_ev = event[elabel][eindex]
        ev = (scale * raw_ev)
        return ev

    def stream(self):
        event = self.instream.stream()
        if event is None:
            return None
        current = dict((k,0) for k in self.settings.keys())
        for k in self.settings.keys():
            if k[0] == '_':
                continue
            p = self.prev[k] if k in self.prev else 0
            current[k] = sum(self.get_val(k,event,x) for x in settings[k])
            if abs(current[k]) < 0.05:
                current[k] = 0
        self.prev = current
        return current

def linux_produce_mouse_event(settings,old,event):
    device = settings['_device']
    if len(event):
        if 'mouse_x' or 'mouse_y' in event:
            event['mouse_x'] = event['mouse_x'] if 'mouse_x' in event else 0
            event['mouse_y'] = event['mouse_y'] if 'mouse_y' in event else 0
            if event['mouse_x'] != 0 or event['mouse_y'] != 0:
                device.emit(uinput.REL_X, int(event['mouse_x']), syn=False)
                device.emit(uinput.REL_Y, int(event['mouse_y']))
        button_sets = {
            'mouse_button_left': uinput.BTN_LEFT,
            'mouse_button_right': uinput.BTN_RIGHT,
            'mouse_button_middle': uinput.BTN_MIDDLE
        }
        for key in button_sets.keys():
            event[key] = event[key] if key in event else 0
            old[key] = old[key] if key in old else 0
            if (old[key] > 0.5) != (event[key] > 0.5):
                device.emit(button_sets[key], int(event[key] > 0.5))
        if 'mouse_wheel' in event:
            if event['mouse_wheel'] != 0:
                device.emit(uinput.REL_WHEEL, int(event['mouse_wheel']))
    return event

def linux_produce_keybd_event(settings,old,event):
    device = settings['_device']
    allkeys = {
        'shift':uinput.KEY_LEFTSHIFT,
        'ctrl':uinput.KEY_LEFTCTRL,
        'alt':uinput.KEY_LEFTALT
    }
    if len(event):
        for key in allkeys.keys():
            event_flags = 0
            if key in event:
                old[key] = old[key] if key in old else 0
                if (old[key] > 0.5) != (event[key] > 0.5):
                    down = 1 if event[key] < 0.5 else 0
                    device.emit(allkeys[key], down)
    return event

job = GamePadInput()
if len(sys.argv) > 1:
    job.attach(int(sys.argv[1]))
    settings = {
        'mouse_x':[['axes',0,8],['hats',0,2]],
        'mouse_y':[['axes',1,8],['hats',1,-2]],
        'mouse_wheel':[['axes',4,2]],
        'mouse_button_left':[['buttons',0]],
        'shift':[['buttons',4]],
        'mouse_button_right':[['buttons',1]],
        'ctrl':[['buttons',5]]
    }
    if len(sys.argv) > 2:
        settings = json.load(open(sys.argv[2]))

    settings['_device'] = uinput.Device([uinput.REL_X, uinput.REL_Y, uinput.BTN_LEFT, uinput.BTN_RIGHT, uinput.BTN_MIDDLE, uinput.REL_WHEEL])
        
    r = rate_limiter(lambda x,y: x['serial'] == y['serial'],[(250,0.01),(250,0.1),(None,1)], job)
    r = TranslateMouse(settings,r)
    old_mouse, old_keybd = { }, { }
    for event in iter(r.stream, None):
        old_keybd = linux_produce_keybd_event(settings,old_keybd,event)
        old_mouse = linux_produce_mouse_event(settings,old_mouse,event)
else:
    print job.sticks
