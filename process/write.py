# python3 write.py

from collections import defaultdict
import datetime
import gzip
import json
import math
import os

import mercantile

import constants
import wpmaps_pb2

MAXZOOM=15
LATLON = 100000
MAXLAT = 89.99999
LOGRANKFACTOR = 750
MINPOI = 50
MAXPOI = 150

def wpmap(poi: dict) -> wpmaps_pb2.WikiGeoData:
  proto = wpmaps_pb2.WikiGeoData()
  proto.q_id = int(poi['q'].lstrip('Q'))
  proto.name = poi['t']
  proto.longitude = round(poi['longitude'] * LATLON)
  proto.latitude = round(max(min(poi['latitude'], MAXLAT), -MAXLAT) * LATLON)
  proto.logrank = round(LOGRANKFACTOR * math.log(max(poi.get('k', 1), 1)))
  return proto

def read_joined(filename: str = constants.JOINED_FILE) -> list[dict]:
  with gzip.open(filename, "rt") as f:
    allpoints = [json.loads(line.strip()) for line in f]
  for p in allpoints:
    p['pbf'] = wpmap(p)
  # already sorted by popularity descending
  return allpoints

def write_some_tiles(allpoints: list[dict], zoom: int) -> list[mercantile.Tile]:
  tiles_written = []
  tiledict = defaultdict(list)
  for p in allpoints:
    t = mercantile.tile(p['longitude'], max(min(p['latitude'], MAXLAT), -MAXLAT), zoom)
    if len(tiledict[t]) < MAXPOI or zoom == MAXZOOM:
      tiledict[t].append(p['pbf'])
  for t, pblist in tiledict.items():
    if len(pblist) < MINPOI:
      continue
    tileproto = wpmaps_pb2.WikiGeoDataList()
    tileproto.items.extend(pblist)
    destination = os.path.join(constants.PATH_TO_TILE_DIR,
      str(t.z), str(t.x), f'{t.y}.pbf')
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(destination, "wb") as f:
      f.write(tileproto.SerializeToString())
    tiles_written.append(t)
  return tiles_written


def loop_over_zoom(allpoints: list[dict]) -> dict[int, list]:
  tiles_written = {}
  for z in range(MAXZOOM, -1, -1):
    print(f'{datetime.datetime.now().isoformat()} - write_some_tiles -> {z}')
    tiles_written[z] = write_some_tiles(allpoints, z)
  return tiles_written



if __name__ == "__main__":
  print(f'{datetime.datetime.now().isoformat()} - read_joined')
  allpoints = read_joined()

  print(f'{datetime.datetime.now().isoformat()} - loop_over_zoom')
  tiles_written = loop_over_zoom(allpoints)

  print(tiles_written)