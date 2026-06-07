import datetime
import gzip
import orjson
import os
import subprocess
import threading
import time

import constants

INPUT_FILE = "/mnt/chromeos/MyFiles/Downloads/latest-all.json.bz2"
REJECT_FILE = "rejected_entries.jsonl.gz"
PROGRESS_FILE = "download_progress_p.txt"
CHUNK_SIZE = 1024 * 1024 * 16 # 16 MB
COORD_PROP_BYTES = b'"P625"'
SUBCLASS_PROP_BYTES = b'"P279"'
current_bytes = 0
coords_written = 0
rejects_written = 0
subclasses_written = 0


def process_file(input_filename: str = INPUT_FILE):
  global coords_written
  global rejects_written
  global subclasses_written
  with open(input_filename, "rb") as bz:
    def file_chunk_generator():
      while True:
        compressed_bytes_chunk = bz.read(CHUNK_SIZE)
        if not compressed_bytes_chunk:
          break
        yield compressed_bytes_chunk

    print("Decompressing stream:")
    try:
      for decompressed_line_bytes in stream_to_lbzip2(file_chunk_generator()):
        if not decompressed_line_bytes:
          continue
        extract_wikidata(decompressed_line_bytes)
        global current_bytes
        save_progress(current_bytes)
        print(f"\rProcessed {current_bytes / (1024**3):.2f} GB of stream, wrote ({coords_written}, {rejects_written}, {subclasses_written})...",
        end="", flush=True)
    except subprocess.CalledProcessError as e:
      print(f"\nError running lbzip2: {e.stderr}")


def download_stream():
  global coords_written
  global rejects_written
  global subclasses_written
  start_byte = get_resume_byte()
  headers = {}
  if start_byte > 0:
    print(f"Resuming download from byte offset: {start_byte}...")
    headers["Range"] = f"bytes={start_byte}-"
  else:
    print("Starting download from the beginning...")

  try:
    response = requests.get(constants.WIKIDATA_ENTITIES_URL, headers=headers, stream=True, timeout=30)
    if response.status_code == 416:
      print("Finished or range invalid.")
      return
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
  # 1. current_bytes: where we are currently reading
  # 2. last_good_byte: the safe checkpoint before the current compression block
  current_bytes = start_byte
  last_good_byte = start_byte
  buffer = b''
  try:
    for decompressed_line_bytes in stream_to_lbzip2(response.iter_content(
        chunk_size=CHUNK_SIZE
      )):
      if not decompressed_line_bytes:
        continue
      try:
        extract_wikidata(decompressed_line_bytes)
        save_progress(current_bytes)
        last_good_byte = current_bytes
      except (ValueError, OSError) as e:
        print(f"\n[!] Decompression error encountered: {e}")
        print(f"Rolling back network stream to last known good checkpoint: {last_good_byte}")
        response.close()
        print("Waiting 10 seconds before automated retry...")
        time.sleep(10)
        return download_stream()
      print(f"\rProcessed {current_bytes / (1024**3):.2f} GB of stream, wrote ({coords_written}, {rejects_written}, {subclasses_written})...",
            end="",
            flush=True
        )
  except (requests.exceptions.RequestException, ConnectionResetError) as e:
    print(f"\n[!] Network dropped: {e}")
    print("Progress safely saved. Run the script again to resume.")
  finally:
    response.close()


def stream_to_lbzip2(compressed_chunks, chunk_size=65536) -> Iterable[bytes]:
  """
  Streams compressed bz2 chunks into lbzip2 and yields decompressed text chunks.

  :param compressed_chunks: An iterable (like a list or generator) of bytes.

  yields string
  """
  global current_bytes
  current_bytes = 0
  # Start the lbzip2 process in decompression mode (-d)
  # -c outputs to stdout instead of a file
  process = subprocess.Popen(
    ['lbzip2', '-d', '-c'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
  )

  # Define a helper function to write data in a background thread.
  # This prevents deadlocking if lbzip2 fills the stdout buffer.
  def writer():
    global current_bytes
    try:
      for compressed_bytes_chunk in compressed_chunks:
        if compressed_bytes_chunk:
          process.stdin.write(compressed_bytes_chunk)
          current_bytes += len(compressed_bytes_chunk)
      process.stdin.close()  # Signal EOF to lbzip2
    except BrokenPipeError:
      # Occurs if lbzip2 exits early (e.g., due to an error)
      pass

  writer_thread = threading.Thread(target=writer)
  writer_thread.start()

  try:
    for decompressed_line_bytes in process.stdout:
      yield decompressed_line_bytes
  finally:
    writer_thread.join()
    process.wait()
    if process.returncode != 0:
      stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
      raise subprocess.CalledProcessError(
        process.returncode, process.args, stderr=stderr_output
      )


def extract_wikidata(line: bytes):
  if not COORD_PROP_BYTES in line and not SUBCLASS_PROP_BYTES in line:
    return
  line.strip()
  if line.endswith(b","):
    line = line[:-1]
  try:
    entity = orjson.loads(line.decode('utf-8', errors='ignore'))
    if "claims" in entity and "P625" in entity["claims"]:
      q_id = entity["id"]
      sitelinks = entity.get("sitelinks", {})
      enwiki = sitelinks.get("enwiki", {}).get("title")
      coords = entity['claims']['P625'].get("mainsnak").get("datavalue").get("value")
      classes = [v.get("mainsnak").get("datavalue").get("value").get("numeric-id") for v in entity['claims']['P31']] if 'P31' in entity['claims'] else []

      if q_id and enwiki and coords and coords['globe'].endswith('/Q2') and 'latitude' in coords and 'longitude' in coords:
        record = {'q': q_id, 't': enwiki, 'y': coords['latitude'], 'x': coords['longitude'], 'c': classes}
        with gzip.open(constants.WIKIDATA_COORDS_EXTRACT_FILE, "at", encoding="utf-8") as earth_coords:
          earth_coords.write(f"{orjson.dumps(record)}\n")
          global coords_written
          coords_written += 1
      else:
        with gzip.open(REJECT_FILE, "at", encoding="utf-8") as reject:
          reject.write(f'{line}\n')
          global rejects_written
          rejects_written += 1
    if SUBCLASS_PROP_BYTES in line:
      with gzip.open(constants.WIKIDATA_SUBCLASS_EXTRACT_FILE, "at", encoding="utf-8") as subclass:
        subclass.write(f'{line}\n')
        global subclasses_written
        subclasses_written += 1
  except json.JSONDecodeError:
    pass


def get_resume_byte():
  """Reads the last successfully saved byte offset from the progress file."""
  if os.path.exists(PROGRESS_FILE):
    try:
      with open(PROGRESS_FILE, "r") as f:
        return int(f.read().strip())
    except ValueError:
      return 0
  return 0


def save_progress(byte_offset):
  """Saves the current byte offset to disk safely."""
  # Write to a temporary file first, then replace to prevent corruption
  temp_file = PROGRESS_FILE + ".tmp"
  with open(temp_file, "w") as f:
    f.write(str(byte_offset))
  os.replace(temp_file, PROGRESS_FILE)


if __name__ == "__main__":
  match len(sys.argv):
    case 1:
      # No argument. Download and process
      download_stream()
    case 2:
      # Argument is a filename. Process the downloaded file.
      input_filename = sys.argv[-1]
      process_file(input_filename)
    case _:
      pass