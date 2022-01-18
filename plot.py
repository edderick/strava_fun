#!/usr/bin/env python

from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw
from datetime import datetime, timedelta
import time
import dateutil.parser
import glob

WIDTH = 750
HEIGHT = 750

BORDER = 10

SPEED = 300
FPS = 12

verbose = False

images = []

gpx_files = glob.glob("*.gpx")

trees = [ET.parse(gpx_file) for gpx_file in gpx_files]

print(f"Processing {len(trees)} file(s)")

# You're smarter than this. -.-
min_lat = float("inf")
max_lat = float("-inf")
min_lon = float("inf")
max_lon = float("-inf")

start_time = None
end_time = None
num_coors = 0

rides = []

for tree in trees:
    ride = {}
    rides.append(ride)

    ride["data"] = []

    for trkpt in tree.iter("{http://www.topografix.com/GPX/1/1}trkpt"):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        time = dateutil.parser.isoparse(
            trkpt.find("{http://www.topografix.com/GPX/1/1}time").text
        )

        ride["data"].append((time, lat, lon))

        min_lat = min(min_lat, lat)
        max_lat = max(max_lat, lat)
        min_lon = min(min_lon, lon)
        max_lon = max(max_lon, lon)

        if start_time is None:
            start_time = time

        # Who cares about efficiency?
        end_time = time

        num_coors += 1

    ride["start_time"] = start_time
    ride["end_time"] = end_time

    start_time = None

print(f"Min Lat: {min_lat}, Max Lat: {max_lat}")
print(f"Min Lon: {min_lon}, Max Lon: {max_lon}")
print(f"Number of co-ords: {num_coors}")

timer = datetime.now()
time_cursor = timedelta()

run_time = timedelta()
for ride in rides:
    run_time = max(ride["end_time"] - ride["start_time"], run_time)

count = 0

im = Image.new("RGB", (WIDTH + BORDER * 2, HEIGHT + BORDER * 2), "white")
pixels = im.load()

while time_cursor < run_time:
    last_cursor = time_cursor
    time_cursor += timedelta(seconds=(1 / FPS) * SPEED)
    count += 1

    if verbose:
        print(f"Frame: {count} at {time_cursor}")

    leaders = []

    for i, ride in enumerate(rides):
        for datum in ride["data"]:
            event_time = datum[0]
            lat = float(datum[1])
            lon = float(datum[2])

            # This result in a bug, need to figure out off by one
            if event_time - rides[i]["start_time"] < last_cursor:
                continue

            x = (lon - min_lon) * (WIDTH / (max_lon - min_lon)) + BORDER
            y = HEIGHT - ((lat - min_lat) * (HEIGHT / (max_lat - min_lat))) + BORDER

            try:
                pixels[x, y] = (255, 0, 0)
            except:
                pass  # TODO: Clip out of bounds

            if event_time - ride["start_time"] > time_cursor:
                leaders.append((x, y))
                break

    frame = im.copy()
    for (x, y) in leaders:
        draw = ImageDraw.Draw(frame)
        try:
            draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill="green", outline="green")
        except Exception as e:
            print(f"Sorry: {e}")
            pass  # TODO: Clip out of bounds

    images.append(frame)

print("Done plotting, saving file...")

# Freeze the last frame
for _ in range(0, 50):
    images.append(im.copy())

images[0].save(
    "./animation.gif",
    save_all=True,
    append_images=images[1:],
    optimize=True,
    duration=1 / FPS,
    loop=0,
)

print(f"Generated {len(images) - 50} frames in {datetime.now() - timer}")
