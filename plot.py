#!/usr/bin/env python

from xml.etree import ElementTree as ET

import tkinter
import time

WIDTH = 500
HEIGHT = 500

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

for trkpt in tree.iter('{http://www.topografix.com/GPX/1/1}trkpt'):
	lat = float(trkpt.get('lat'))
	lon = float(trkpt.get('lon'))
	min_lat = min(min_lat, lat)
	max_lat = max(max_lat, lat)
	min_lon = min(min_lon, lon)
	max_lon = max(max_lon, lon)

print(f"{min_lat}, {max_lat} -- {min_lon}, {max_lon}")

i = 0
for trkpt in tree.iter('{http://www.topografix.com/GPX/1/1}trkpt'):
	lat = float(trkpt.get('lat'))
	lon = float(trkpt.get('lon'))
	print(lat, lon)

	x = (lon - min_lon) * (WIDTH / (max_lon - min_lon))
	y = HEIGHT - ((lat - min_lat) * (HEIGHT / (max_lat - min_lat)))

	plot_coord(x, y, size=1)

	# TODO: figure out why update() is slow; remove this hack
	i += 1
	if i % 10 == 0:
		root.update()

print('Done plotting, entering the main loop')

# Keep the tk window alive...
tkinter.mainloop()
