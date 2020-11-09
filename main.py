
import os
#import logging
#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

############ Magic Configs
target_fps = 30
size = (500,200) # half of is 100 for nice midpoint

font_path =  "Pixel LCD-7.ttf"
font_size = 40 # 140 for big mid screen, 40 for

fudge_factor = 1
line_width = 7

vert_scale = 10 # makes peaks bigger - change if you change the size

pulse_parts = [0,1,0,0,6,0,-5,0,0,-1,0,0,2,0] # distinctive heart beat

BACKGROUND_COLOR = (0,0,0,255)
LINE_COLOR = (0,255,0,250)
FONT_COLOR = (0,255,0)

fade_factor = 253 # number between 0 and 255. Probably 250-255 ish


def position_font(screen_size, text_size):
    # middle of screen:
    #return  ((screen_size[0] - text_size[0] )// 2, (screen_size[1] - text_size[1])//2)

    # Bottom right
    return screen_size[0] - text_size[0] - 2 , screen_size[1] - text_size[1] - 2
    
############ DONT EDIT BELOW THIS

from datetime import datetime, timedelta

from time import sleep
from ant.easy.node import Node
from ant.easy.channel import Channel
from ant.base.message import Message

import threading
import pygame

## statics

NETWORK_KEY= [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]

pygame.init()

screen = pygame.display.set_mode(size, flags=pygame.NOFRAME)
pygame.display.set_caption("Heartbeat")

back_font = pygame.font.Font(font_path, font_size)

clock = pygame.time.Clock()

alive = True

HEART_EVENT_TYPE = pygame.event.custom_type()

# ANT stuff

def on_data(data):
    heart_speed = data[7] * fudge_factor
    print("Heart speed detected: %s" % heart_speed)
    ev = pygame.event.Event(HEART_EVENT_TYPE, {'speed': heart_speed})

    pygame.event.post(ev)


def back_thread(node):
    node.set_network_key(0x00, NETWORK_KEY)
    channel = node.new_channel(Channel.Type.BIDIRECTIONAL_RECEIVE)

    channel.on_broadcast_data = on_data
    channel.on_burst_data = on_data

    # magic numbers
    channel.set_period(16070) # was 8070
    channel.set_search_timeout(20) # was 12
    channel.set_rf_freq(57)
    channel.set_id(0, 120, 0)

    try:
        channel.open()
        node.start()
    finally:
        node.stop()
        print("Ant Node shutdown complete")

node = Node()
x = threading.Thread(target=back_thread, args=(node,))
x.start()

last_seen = datetime.now()

drawing = pygame.Surface(screen.get_size(), flags=pygame.SRCALPHA)
drawing.fill((0,0,0,255))

alpha_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
alpha_surf.fill((255, 255, 255, fade_factor))
  
ptr = -1
last_height = 100
last_pulse = datetime.now()
pulse_time = 10
heart_speed = -1
offset = -1

fade_factor = 255
time_since_seen = timedelta(seconds=100)


while alive:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            alive=False
            node.stop()
        elif event.type == HEART_EVENT_TYPE:
            print("Heart speed detected! %s" % event.speed)
            heart_speed = event.speed
            if event.speed != 0:
                pulse_time =  60 / event.speed
            last_seen = datetime.now()
        elif event.type == pygame.KEYDOWN:
            print("KEy pressed - closing")
            pygame.display.quit()
            alive = False
            node.stop()

    time_since_seen = datetime.now() - last_seen

    next_ptr = ptr + 5

    screen.fill(BACKGROUND_COLOR)
    #alpha_surf.fill((0,0,0,fade_factor))

    now = datetime.now()
    tt = now - last_pulse
    if tt.total_seconds() > pulse_time:
        offset = -1
        last_pulse = now

    offset += 1
    #print(offset)

    if offset >= len(pulse_parts)-1:
        height = size[1]//2
    else:
        height = (size[1]//2)  -(vert_scale * pulse_parts[offset])
    #print(height)

    if time_since_seen.total_seconds() < 10:
        
        drawing.blit(alpha_surf, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        pygame.draw.line(drawing, LINE_COLOR, [ptr, last_height], [next_ptr, height], line_width)
    
        display_text = "%s" % round(heart_speed)
        text = back_font.render(display_text, False, FONT_COLOR)
        text_pos = position_font(size, (text.get_width(),text.get_height()))
        screen.blit(text, text_pos)
        
        screen.blit(drawing,(0,0))

    pygame.display.flip()

    if next_ptr > size[0]:
        ptr = -5
    else:
        ptr = next_ptr
    last_height = height
            
    clock.tick(30)
