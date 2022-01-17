#!/usr/bin/python3

from xml.etree import ElementTree as ET

tree = ET.parse('./Just_Keep_Going_Past_the_Library_.gpx')

for trkpt in tree.iter('{http://www.topografix.com/GPX/1/1}trkpt'):
  print(trkpt.get('lat'), trkpt.get('lon'))



