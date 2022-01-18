#!/usr/bin/env python

from xml.etree import ElementTree as ET

import tkinter
import time
import threading
import dateutil.parser
import math
from datetime import datetime, timedelta

from PIL import Image, ImageDraw

WIDTH = 500
HEIGHT = 500

SPEED = 300
FPS = 12

images = []

trees = [
    ET.parse('./Just_Keep_Going_Past_the_Library_.gpx'), 
    ET.parse('./Just_Checking_New_York_is_Still_There.gpx'),
    ET.parse('./Citibike_be_slow_yo.gpx'),
    ET.parse('./Nowhere_in_Particular.gpx'),
    ET.parse('./Christmas_Ride.gpx'),
    ET.parse('./PPx5.gpx'),
]

print(f'Processing {len(trees)} file(s)')

# You're smarter than this. -.-
min_lat = float('inf')
max_lat = float('-inf')
min_lon = float('inf')
max_lon = float('-inf')

start_time = None
end_time = None
num_coors = 0

start_times = []
end_times = []

for tree in trees:
    for trkpt in tree.iter('{http://www.topografix.com/GPX/1/1}trkpt'):
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        min_lat = min(min_lat, lat)
        max_lat = max(max_lat, lat)
        min_lon = min(min_lon, lon)
        max_lon = max(max_lon, lon)

        if start_time is None:
            start_time = dateutil.parser.isoparse(trkpt.find('{http://www.topografix.com/GPX/1/1}time').text)
        
        # Who cares about efficiency?
        end_time = dateutil.parser.isoparse(trkpt.find('{http://www.topografix.com/GPX/1/1}time').text)
    
        num_coors += 1

    start_times.append(start_time)
    end_times.append(end_time)

    start_time=None

print(f"{min_lat}, {max_lat} -- {min_lon}, {max_lon}")
print(f"Number of co-ords: {num_coors}")
#print(f"Start time: {start_time}, End time: {end_time}")

timer = datetime.now()

time_cursor = timedelta()

run_time = timedelta()
for start, end in zip(start_times, end_times):
    run_time = max(end - start, run_time)


count = 0

im = Image.new('RGB', (WIDTH, HEIGHT), 'white')
draw = ImageDraw.Draw(im)
pixels = im.load()

last_x = [None for _ in trees]
last_y = [None for _ in trees]


while  time_cursor < run_time:
    last_cursor = time_cursor
    time_cursor += timedelta(seconds=(1/FPS)*SPEED) 
    count+=1
    print(f'Frame: {count} at {time_cursor}')

    for i, tree in enumerate(trees):

        # clearour the leader TODO: Find more elegant way
        x = last_x[i]
        y = last_y[i]
        if x and y:
            try:
                pixels[x, y] = (255, 0, 0)
                pixels[x+1, y] = (255, 255, 255)
                pixels[x+1, y+1] = (255, 255, 255)
                pixels[x, y+1] = (255, 255, 255)
            except: 
                pass


        for trkpt in tree.iter('{http://www.topografix.com/GPX/1/1}trkpt'):
            event_time = dateutil.parser.isoparse(trkpt.find('{http://www.topografix.com/GPX/1/1}time').text)

            # This result in a bug, need to figure out off by one
            if event_time - start_times[i] < last_cursor:
                continue

            lat = float(trkpt.get('lat'))
            lon = float(trkpt.get('lon'))
            #print(lat, lon)

            x = (lon - min_lon) * (WIDTH / (max_lon - min_lon))
            y = HEIGHT - ((lat - min_lat) * (HEIGHT / (max_lat - min_lat)))

            last_x[i] = x
            last_y[i] = y
    
            #frame.ellipse((x, y, x+1, y+1), fill=red)
            try: 
                pixels[x, y] = (255, 0, 0)
            except: 
                pass # TODO: Clip out of bounds

            if event_time - start_times[i] > time_cursor: 
                try:
                    pixels[x, y] = (0, 255, 0)
                    pixels[x+1, y] = (0, 255, 0)
                    pixels[x+1, y+1] = (0, 255, 0)
                    pixels[x, y+1] = (0, 255, 0)
                except: 
                    pass # TODO: Clip out of bounds
                break

    images.append(im.copy())

print('Done plotting, entering the main loop')

print(len(images))

# Freeze the last frame
for _ in range(1, 50): 
    images.append(im.copy())

images[0].save('./pillow_imagedraw.gif',
               save_all=True, append_images=images[1:], optimize=True, duration=1/FPS, loop=0)

print(f'Generated in {datetime.now() - timer}')
