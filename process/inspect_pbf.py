import sys

import constants
import wpmaps_pb2

def get_proto_file_contents(path_to_file: str) -> Any:
  try:
    with open(path_to_file, "rb") as f:
      data = f.read()

    if constants.TILE_SET_LIST_FILENAME in path_to_file:
      tsl = wpmaps_pb2.TileSetList()
      tsl.ParseFromString(data)
      print(tsl)
    else:
      wgdl = wpmaps_pb2.WikiGeoDataList()
      wgdl.ParseFromString(data)
      print(wgdl)
  except FileNotFoundError:
    print(f'Failed to find {path_to_file}')
  except Exception as e:
    print(f'Failed to parse protobuf from {path_to_file}: {e}')


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"Usage: python3 {sys.argv[0]} path/to/tile.pbf ...")
    sys.exit(1)

  for path in sys.argv[1:]:
    print(get_proto_file_contents(path))