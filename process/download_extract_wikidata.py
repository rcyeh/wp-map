import json
import os
import subprocess
import threading
import time

URL = "https://dumps.wikimedia.org/wikidatawiki/entities/latest-all.json.bz2"
INPUT_FILE = "/mnt/chromeos/MyFiles/Downloads/latest-all.json.bz2"
OUTPUT_FILE = "extracted_data_p.csv"
PROGRESS_FILE = "download_progress_p.txt"
CHUNK_SIZE = 512 * 1024  # 512 KB
current_bytes = 0


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


def stream_to_pbzip2(compressed_chunks, chunk_size=65536):
    """
    Streams compressed bz2 chunks into pbzip2 and yields decompressed text chunks.
    
    :param compressed_chunks: An iterable (like a list or generator) of bytes.
    """
    global current_bytes
    current_bytes = 0
    # Start the pbzip2 process in decompression mode (-d)
    # -c outputs to stdout instead of a file
    process = subprocess.Popen(
        ['pbzip2', '-d', '-c'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Define a helper function to write data in a background thread.
    # This prevents deadlocking if pbzip2 fills the stdout buffer.
    def writer():
        global current_bytes
        try:
            for chunk in compressed_chunks:
                if chunk:
                    process.stdin.write(chunk)
                    current_bytes += len(chunk)
            process.stdin.close()  # Signal EOF to pbzip2
        except BrokenPipeError:
            # Occurs if pbzip2 exits early (e.g., due to an error)
            pass

    # Start the writer thread
    writer_thread = threading.Thread(target=writer)
    writer_thread.start()

    # Read the decompressed stream from stdout chunk by chunk
    try:
        while True:
            # Read a chunk of decompressed bytes
            decompressed_bytes = process.stdout.read(chunk_size)
            if not decompressed_bytes:
                break
            
            # Decode to text (adjust encoding if your data isn't utf-8)
            yield decompressed_bytes.decode('utf-8', errors='replace')
    finally:
        # Clean up the process and thread
        writer_thread.join()
        process.wait()
        
        # Check for errors
        if process.returncode != 0:
            stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
            raise subprocess.CalledProcessError(
                process.returncode, process.args, stderr=stderr_output
            )


def extract_wikidata(buffer: str):
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        line = line.strip()

        if line.startswith("[") or line == "]":
            continue
        if line.endswith(","):
            line = line[:-1]
        if not line:
            continue

        try:
            entity = json.loads(line)
            if "claims" in entity and "P625" in entity["claims"]:
                q_id = entity["id"]
                sitelinks = entity.get("sitelinks", {})
                enwiki = sitelinks.get("enwiki", {}).get("title")

                if enwiki:
                    with open(OUTPUT_FILE, "at", encoding="utf-8") as out:
                        out.write(f"{q_id}|{enwiki}|{entity['claims']['P625']}\n")
        except json.JSONDecodeError:
            continue


def process_file(input_filename: str = INPUT_FILE):
    with open(input_filename, "rb") as bz:
        def file_chunk_generator():
            while True:
                chunk = bz.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

        print("Decompressing stream:")
        buffer = ''
        try:
            for text_chunk in stream_to_pbzip2(file_chunk_generator()):
                buffer += text_chunk
                extract_wikidata(buffer)

                # Periodically write current progressive byte (not checkpoint byte) to disk
                global current_bytes
                save_progress(current_bytes)
                print(f"\rProcessed {current_bytes / (1024**3):.2f} GB of compressed stream...", end="", flush=True)
        except subprocess.CalledProcessError as e:
            print(f"\nError running pbzip2: {e.stderr}")


def download_stream():
    # Load progress
    start_byte = get_resume_byte()
    headers = {}
    
    if start_byte > 0:
        print(f"Resuming download from byte offset: {start_byte}...")
        headers["Range"] = f"bytes={start_byte}-"
    else:
        print("Starting download from the beginning...")

    try:
        response = requests.get(URL, headers=headers, stream=True, timeout=30)
        if response.status_code == 416:
            print("Finished or range invalid.")
            return
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    # Track two positions: 
    # 1. current_bytes: where we are currently reading
    # 2. last_good_byte: the safe checkpoint before the current compression block
    current_bytes = start_byte
    last_good_byte = start_byte 
    
    buffer = ""

    try:
        for text_chunk in stream_to_pbzip2(response.iter_content(
                chunk_size=CHUNK_SIZE
            )):
            current_bytes += len(CHUNK_SIZE)
            if not text_chunk:
                continue
            
            try:
                # Attempt to decompress the incoming network chunk
                buffer += text_chunk
                extract_wikidata(buffer)
                
                # If decompression succeeded, this chunk was safely processed.
                # Update our absolute position tracker.
                save_progress(current_bytes)
                
                # If the decompressor has completely finished a BZ2 stream block 
                # and is waiting for a new one, we can safely checkpoint this position.
                last_good_byte = current_bytes

            except (ValueError, OSError) as e:
                # This catches block alignment issues, truncation errors, or corruption
                print(f"\n[!] Decompression error encountered: {e}")
                print(f"Rolling back network stream to last known good checkpoint: {last_good_byte}")
                
                # Close the broken response stream
                response.close()
                
                # Backoff delay to let the network settle down or avoid spamming the server
                print("Waiting 10 seconds before automated retry...")
                time.sleep(10)
                
                # Recursively restart the stream loop from the safe position
                return download_stream()

            # Periodically write current progressive byte (not checkpoint byte) to disk
            save_progress(current_bytes)
            print(f"\rProcessed {current_bytes / (1024**3):.2f} GB of compressed stream...", end="", flush=True)

    except (requests.exceptions.RequestException, ConnectionResetError) as e:
        print(f"\n[!] Network dropped: {e}")
        print("Progress safely saved. Run the script again to resume.")
    finally:
        response.close()


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
    
