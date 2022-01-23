#!/usr/bin/env python

from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from fit_reader import FitFileReader
import time
import dateutil.parser
import glob

# TODO: Argparse
DARK_MODE = True
WIDTH = 750
HEIGHT = 750
BORDER = 10
SPEED = 300
FPS = 12
VERBOSE = True

MAX_STARTING_LAT = 180
MIN_STARTING_LAT = -180
MAX_STARTING_LON = 180
MIN_STARTING_LON = -180

MAX_DURATION = 60  # Minutes

font = ImageFont.truetype("Helvetica.ttc", size=22)

# TODO: Parameterize
gpx_files = glob.glob("./gpx/*.gpx")
fit_files = glob.glob("./all_data/export_14668556/activities/*.fit.*")

gpx_trees = [ET.parse(gpx_file) for gpx_file in gpx_files]

print(f"Processing {len(gpx_files) + len(fit_files)} file(s)")

# You're smarter than this. -.-
min_lat = float("inf")
max_lat = float("-inf")
min_lon = float("inf")
max_lon = float("-inf")

start_time = None
end_time = None
num_points = 0

rides = []

activities = []

for tree in gpx_trees:
    records = []

    for trkpt in tree.iter("{http://www.topografix.com/GPX/1/1}trkpt"):
        time = dateutil.parser.isoparse(
            trkpt.find("{http://www.topografix.com/GPX/1/1}time").text
        )
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        records.append((time, lat, lon))

    activities.append({"filename": "TODO.gpx", "records": records})

reader = FitFileReader()
for fit_file in fit_files:
    try:
        records = reader.process_fit_file(fit_file)
        activities.append({"filename": fit_file, "records": records})
    except Exception as e:
        print(f"Skipping file {fit_file} due to error: {e}")

for activity in activities:
    filename = activity["filename"]
    records = activity["records"]

    if len(records) == 0:
        print(f"Skipping file {filename}. Contains no records.")
        continue

    if (
        records[0][1] > MAX_STARTING_LAT
        or records[0][1] < MIN_STARTING_LAT
        or records[0][2] > MAX_STARTING_LON
        or records[0][2] < MIN_STARTING_LON
    ):
        print(f"Skipping file {filename}. Our of bounds.")
        continue

    if (records[-1][0] - records[0][0]).total_seconds() / 60 > MAX_DURATION:
        print(f"Skipping file {filename}. Activity too long")
        continue

    data = []

    for record in records:
        time, lat, lon = record
        data.append((time, lat, lon))

        min_lat = min(min_lat, lat)
        max_lat = max(max_lat, lat)
        min_lon = min(min_lon, lon)
        max_lon = max(max_lon, lon)

        if start_time is None:
            start_time = time

        # Who cares about efficiency?
        end_time = time

        num_points += 1

    ride = {}
    rides.append(ride)

    ride["data"] = data

    ride["start_time"] = start_time
    ride["end_time"] = end_time

    start_time = None

print(f"Min Lat: {min_lat}, Max Lat: {max_lat}")
print(f"Min Lon: {min_lon}, Max Lon: {max_lon}")
print(f"Number of coordinates: {num_points}")
print(f"Number of rides: {len(rides)}")

timer = datetime.now()
time_cursor = timedelta()

run_time = timedelta()
for ride in rides:
    run_time = max(ride["end_time"] - ride["start_time"], run_time)

count = 0

images = []

im = Image.new(
    "RGB", (WIDTH + BORDER * 2, HEIGHT + BORDER * 2), "Black" if DARK_MODE else "White"
)
pixels = im.load()

while time_cursor < run_time:
    last_cursor = time_cursor
    time_cursor += timedelta(seconds=(1 / FPS) * SPEED)
    count += 1

    if VERBOSE:
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

            px = pixels[x, y]
            delta = (65, 0, 0) if DARK_MODE else (0, -65, -65)
            pixels[x, y] = (px[0] + delta[0], px[1] + delta[1], px[2] + delta[2])

            if event_time - ride["start_time"] > time_cursor:
                leaders.append((x, y))
                break

    frame = im.copy()
    draw = ImageDraw.Draw(frame)
    try:
        draw.text(
            (WIDTH - 65, HEIGHT - 15),
            f"{time_cursor}",
            fill=(200, 200, 200),
            align="right",
            font=font,
        )
    except:
        pass  # Don't worry about failed fonts
    for (x, y) in leaders:
        draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill="green", outline="green")

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
