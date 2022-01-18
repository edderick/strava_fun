#!/usr/bin/env python

from xml.etree import ElementTree as ET

import tkinter
import time
import threading
import dateutil.parser
import math
from datetime import datetime

WIDTH = 500
HEIGHT = 500

SPEED = 300

root = tkinter.Tk()
myCanvas = tkinter.Canvas(root, bg="white", height=HEIGHT, width=WIDTH)
myCanvas.pack()

def plot_coord(x, y, size=5):
	arc = myCanvas.create_oval(x, y, x+size, y+size, fill='red', outline='red')

tree = ET.parse('./Just_Keep_Going_Past_the_Library_.gpx')

# You're smarter than this. -.-
min_lat = float('inf')
max_lat = float('-inf')
min_lon = float('inf')
max_lon = float('-inf')

start_time = None
num_coors = 0

for trkpt in tree.iter('{http://www.topografix.com/GPX/1/1}trkpt'):
	lat = float(trkpt.get('lat'))
	lon = float(trkpt.get('lon'))
	min_lat = min(min_lat, lat)
	max_lat = max(max_lat, lat)
	min_lon = min(min_lon, lon)
	max_lon = max(max_lon, lon)

	if start_time is None:
		start_time = dateutil.parser.isoparse(trkpt.find('{http://www.topografix.com/GPX/1/1}time').text)
	
	num_coors += 1

print(f"{min_lat}, {max_lat} -- {min_lon}, {max_lon}")
print(f"Number of co-ords: {num_coors}")

real_start_time = datetime.now()

def do_thread():
	i = 0
	for trkpt in tree.iter('{http://www.topografix.com/GPX/1/1}trkpt'):
		lat = float(trkpt.get('lat'))
		lon = float(trkpt.get('lon'))
		#print(lat, lon)

		x = (lon - min_lon) * (WIDTH / (max_lon - min_lon))
		y = HEIGHT - ((lat - min_lat) * (HEIGHT / (max_lat - min_lat)))

		plot_coord(x, y, size=1)

		event_time = dateutil.parser.isoparse(trkpt.find('{http://www.topografix.com/GPX/1/1}time').text)

		expected_time = (event_time - start_time) / SPEED
		elapsed_time = datetime.now() - real_start_time

		print(expected_time, elapsed_time)
		
		if elapsed_time < expected_time:
			print(f'Sleep for {expected_time - elapsed_time}')
			time.sleep((expected_time - elapsed_time).total_seconds())

	print('Done plotting, entering the main loop')

t = threading.Thread(target=do_thread)
t.start()
root.mainloop()	

# Keep the tk window alive...
t.join()
