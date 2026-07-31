import datetime
import gzip

import os
import subprocess
import sys
import threading
import time

import orjson
import requests

import constants


CLASS_MAPPING_FILE = "process/class_mapping.jsonl.gz"

# Global mapping cache: class_id_str -> category_string
class_category_map: dict[str, str] = {}
category_code_map: dict[str, int] = {
  "unknown": 0,
  "administrative": 1,
  "building": 2,
  "cultural": 3,
  "event": 4,
  "natural": 5,
  "transportation": 6,
}

_mapping_lock = threading.Lock()


def load_class_mapping():
  """Read class_mapping.jsonl.gz into memory on startup."""
  global class_category_map
  if not os.path.exists(CLASS_MAPPING_FILE):
    sys.stderr.write(f"Warning: {CLASS_MAPPING_FILE} not found; no class categories available.\n")
    return
  with gzip.open(CLASS_MAPPING_FILE, "rt", encoding="utf-8") as f:
    for line in f:
      data = orjson.loads(line.strip())
      # Data is [class_id_int, label_str, category_str]
      cid_str = str(data[0])
      cat = data[2]
      class_category_map[cid_str] = cat
  sys.stderr.write(f"Loaded {len(class_category_map)} class categories from {CLASS_MAPPING_FILE}.\n")


def _append_new_class(cid: int, category: str):
  """Append a new class mapping entry to the file (called only when a truly new class is seen)."""
  label = class_category_map.get(str(cid), "")  # Unknown classes have no pre-existing label
  record = [cid, label, category]
  with _mapping_lock:
    with gzip.open(CLASS_MAPPING_FILE, "at", encoding="utf-8") as f:
      f.write(orjson.dumps(record).decode() + "\n")


def classify_classes(class_ids):
  """Build a list of ArticleType codes for this entity and add any unseen classes."""
  result_codes = []
  for cid in class_ids:
    if not isinstance(cid, int):
      continue
    cid_str = str(cid)
    if cid_str not in class_category_map:
      # New class -- add with "unknown"
      class_category_map[cid_str] = "unknown"
      _append_new_class(cid, "unknown")
      result_codes.append(0)  # ARTICLE_TYPE_UNKNOWN
    else:
      cat = class_category_map[cid_str]
      result_codes.append(category_code_map.get(cat, 0))
  return result_codes


INPUT_FILE = "/mnt/chromeos/MyFiles/Downloads/latest-all.json.bz2"
REJECT_FILE = "rejected_entries.jsonl.gz"
PROGRESS_FILE = "download_progress_p.txt"
CHUNK_SIZE = 1024 * 1024 * 16  # 16 MB
COORD_PROP_BYTES = b'"P625"'
SUBCLASS_PROP_BYTES = b'"P279"'
current_bytes = 0
coords_written = 0
rejects_written = 0
subclasses_written = 0


def process_file(input_filename: str = INPUT_FILE):
  start = datetime.datetime.now()
  global coords_written, rejects_written, subclasses_written
  # Load class mapping before processing begins
  load_class_mapping()
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
        now = datetime.datetime.now()
        elapsed = (now - start).seconds
        print(f"\rProcessed {current_bytes / (1024**3):.2f} GB of stream in " +
           f"{elapsed} s (avg {current_bytes / (1024**2) / seconds:.2f} " +
           "MB/s), wrote (" +
           f"{coords_written}, {rejects_written}, {subclasses_written})...",
           end="", flush=True)
    except subprocess.CalledProcessError as e:
      print(f"\nError running lbzip2: {e.stderr}")


def download_stream():
  start = datetime.datetime.now()
  global coords_written, rejects_written, subclasses_written
  # Load class mapping before processing begins
  load_class_mapping()
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
  global current_bytes
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
      now = datetime.datetime.now()
      elapsed = (now - start).seconds
      print(f"\rProcessed {current_bytes / (1024**3):.2f} GB of stream in " +
         f"{elapsed} s (avg {current_bytes / (1024**2) / seconds:.2f} " +
         "MB/s), wrote (" +
         f"{coords_written}, {rejects_written}, {subclasses_written})...",
         end="",
         flush=True
      )
  except (requests.exceptions.RequestException, ConnectionResetError) as e:
    print(f"\n[!] Network dropped: {e}")
    print("Progress safely saved. Run the script again to resume.")
  finally:
    response.close()


def stream_to_lbzip2(compressed_chunks, chunk_size=65536):
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
      # Occurs if lbzip2 exits early (e.g. due to an error)
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
  line = line.strip()
  if line.endswith(b","):
    line = line[:-1]
  try:
    line_str = line.decode('utf-8', errors='ignore')
    entity = orjson.loads(line_str)
    if "claims" in entity and "P625" in entity["claims"]:
      q_id = entity["id"]
      sitelinks = entity.get("sitelinks", {})
      enwiki = sitelinks.get("enwiki", {}).get("title")
      coords = [v.get("mainsnak", {}).get("datavalue", {}).get("value", {}) for v in (entity['claims']['P625'] if isinstance(entity['claims']['P625'], list) else [entity['claims']['P625']])]
      classes = [v.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("numeric-id", {}) for v in entity['claims']['P31']] if 'P31' in entity['claims'] else []

      if q_id and enwiki and coords:
        record = {'q': q_id, 't': enwiki, 'xy': coords, 'c': classes}
        # Classify each class ID into a code + add to record
        codes = classify_classes(classes)
        record['ct'] = codes
        with gzip.open(constants.WIKIDATA_COORDS_EXTRACT_FILE, "at", encoding="utf-8") as earth_coords:
          earth_coords.write(f"{orjson.dumps(record)}\n")
          global coords_written
          coords_written += 1
      else:
        with gzip.open(REJECT_FILE, "at", encoding="utf-8") as reject:
          reject.write(f'{line_str}\n')
          global rejects_written
          rejects_written += 1
    if SUBCLASS_PROP_BYTES in line:
      with gzip.open(constants.WIKIDATA_SUBCLASS_EXTRACT_FILE, "at", encoding="utf-8") as subclass:
        subclass.write(f'{line_str}\n')
        global subclasses_written
        subclasses_written += 1
  except orjson.JSONDecodeError:
    print(f'Failed to decode as JSON: {line_str}')
    with gzip.open(REJECT_FILE, "at", encoding="utf-8") as reject:
      reject.write(f'{line_str}\n')


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
