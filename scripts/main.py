import os
import json
import argparse
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from rrtex_to_tga import convert_rrtex

# This Python script aims to convert a collection of .rrtex files into .tga files.
# The script starts by specifying the source and destination directories where the files are stored and will be saved,respectively.

# In the main part of the script, it first browses the source directory recursively and creates
# a corresponding destination directory for each subdirectory found. Then, it processes all files in each directory,
#  attempting to convert any files with a .rrtex extension using a function called convert_rrtex.
# If the conversion is successful, the script increments the relevant statistics, and if not, it logs the details of the failure.
# Files that are not .rrtex are skipped and logged accordingly.

# Finally, the script outputs the statistics of the conversion process and saves
#  the log report as a JSON file to the specified destination directory.

def save_dict_to_json(dictionary, path, file_name, indent=4):
    """
    Saves a dictionary as JSON to a specified path with a specified file name.

    Args:
        dictionary (dict): The dictionary to save as JSON.
        path (str): The path where the JSON file will be saved.
        file_name (str): The name of the JSON file.
        indent (int): The number of spaces to use for indentation (default is 4).

    Returns:
        None
    """
    # create directory if it does not exist
    if not os.path.exists(path):
        os.makedirs(path)
    # construct the full file path
    file_path = os.path.join(path, file_name)
    # write the dictionary as formatted JSON to file
    with open(file_path, 'w') as json_file:
        json.dump(dictionary, json_file, indent=indent)

def log_details(details, filepath, exception):
    details.append({"path":filepath,"exception":exception})

class ThreadSafeStats:
    """Thread-safe statistics tracking for multithreaded processing"""
    def __init__(self):
        self.lock = threading.Lock()
        self.stats = {
            'rrtex': 0,
            'converted': 0,
            'failed': 0
        }
        self.details = {
            'failed': []
        }

    def increment_rrtex(self):
        with self.lock:
            self.stats['rrtex'] += 1

    def increment_converted(self):
        with self.lock:
            self.stats['converted'] += 1

    def increment_failed(self, filepath, exception):
        with self.lock:
            self.stats['failed'] += 1
            self.details['failed'].append({"path": filepath, "exception": exception})

    def get_stats(self):
        with self.lock:
            return self.stats.copy()

    def get_details(self):
        with self.lock:
            return {
                'failed': self.details['failed'].copy()
            }

def process_file(file_info, image_format, flatten, dest_dir, thread_stats):
    """
    Process a single .rrtex file in a worker thread

    Args:
        file_info: tuple of (src_file, dest_subdir, file_name)
        image_format: output image format (tga, png, etc.)
        flatten: whether to flatten directory structure
        dest_dir: base destination directory
        thread_stats: ThreadSafeStats instance for tracking results

    Returns:
        tuple: (success: bool, file_name: str, error_msg: str or None)
    """
    src_file, dest_subdir, file_name = file_info

    try:
        thread_stats.increment_rrtex()

        # Determine output file path
        if flatten:
            dest_file = os.path.join(dest_dir, file_name + '.' + image_format)
        else:
            dest_file = os.path.join(dest_subdir, file_name + '.' + image_format)

        # Convert the file
        convert_rrtex(src_file, dest_file)
        thread_stats.increment_converted()

        return True, file_name, None

    except Exception as e:
        error_msg = str(e)
        thread_stats.increment_failed(src_file, error_msg)
        return False, file_name, error_msg

if __name__ == "__main__":
    # Detect available CPU cores for default thread count
    default_threads = os.cpu_count() or 4  # fallback to 4 if cpu_count() returns None

    parser = argparse.ArgumentParser(description='Convert rrtex files to tga.')
    parser.add_argument('--src', metavar='--src', type=str, help='path to source directory')
    parser.add_argument('--format', metavar='format', type=str, default='tga', help='image output format (default: tga)')
    parser.add_argument('--flatten', dest='flatten', action='store_true', help='description of parameter (default: False)')
    parser.add_argument('--threads', metavar='threads', type=int, default=default_threads,
                       help=f'number of worker threads (default: {default_threads} - detected CPU cores)')
    parser.set_defaults(flatten=False)

    args = parser.parse_args()

    src_dir = args.src
    image_format = args.format
    flatten = args.flatten
    num_threads = args.threads

    dest_dir = os.path.join(os.getcwd(), 'export/')

    print("Starting image extraction ...")
    print(f"Source directory: {src_dir}")
    print(f"Destination directory: {dest_dir}")
    print(f"CPU cores detected: {os.cpu_count()}")
    print(f"Worker threads: {num_threads}")
    print(f"Output format: {image_format}")
    print(f"Flatten structure: {flatten}")

    # Initialize thread-safe statistics
    thread_stats = ThreadSafeStats()

    # First pass: collect all .rrtex files and create directory structure
    print("Scanning for .rrtex files...")
    file_tasks = []

    for dirpath, dirnames, filenames in os.walk(src_dir):
        # create a corresponding destination directory
        dest_subdir = dirpath.replace(src_dir, dest_dir, 1)
        os.makedirs(dest_subdir, exist_ok=True)

        # collect all .rrtex files for processing
        for file in filenames:
            if '.' in file:  # ensure file has extension
                file_extension = file.split('.')[-1]  # get last extension part
                file_name = '.'.join(file.split('.')[:-1])  # get name without extension

                if file_extension == 'rrtex':
                    src_file = os.path.join(dirpath, file)
                    file_tasks.append((src_file, dest_subdir, file_name))

    total_files = len(file_tasks)
    print(f"Found {total_files} .rrtex files to process")

    if total_files == 0:
        print("No .rrtex files found!")
        sys.exit(0)

    # Second pass: process files with multithreading
    print(f"Processing files with {num_threads} worker threads...")
    start_time = time.time()
    completed_files = 0

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_file, file_info, image_format, flatten, dest_dir, thread_stats): file_info
            for file_info in file_tasks
        }

        # Process completed tasks
        for future in as_completed(future_to_file):
            file_info = future_to_file[future]
            src_file, _, file_name = file_info

            try:
                success, processed_name, error_msg = future.result()
                completed_files += 1

                if success:
                    print(f"[{completed_files}/{total_files}] ✓ {processed_name}")
                else:
                    print(f"[{completed_files}/{total_files}] ✗ {processed_name} - {error_msg}")

                # Show progress every 10 files or at the end
                if completed_files % 10 == 0 or completed_files == total_files:
                    current_stats = thread_stats.get_stats()
                    elapsed = time.time() - start_time
                    rate = completed_files / elapsed if elapsed > 0 else 0
                    print(f"Progress: {completed_files}/{total_files} files, "
                          f"{current_stats['converted']} converted, "
                          f"{current_stats['failed']} failed, "
                          f"{rate:.1f} files/sec")

            except Exception as e:
                print(f"[{completed_files}/{total_files}] ✗ {file_name} - Unexpected error: {e}")
                completed_files += 1

    # Final statistics
    final_stats = thread_stats.get_stats()
    final_details = thread_stats.get_details()
    elapsed_time = time.time() - start_time

    print(f"\n=== Conversion Complete ===")
    print(f"Total time: {elapsed_time:.2f} seconds")
    print(f"Average rate: {completed_files/elapsed_time:.1f} files/sec")
    print(f"Final statistics: {final_stats}")

    logreport = {}
    logreport['stats'] = final_stats
    logreport['details'] = final_details
    logreport['processing_time_seconds'] = elapsed_time
    logreport['files_per_second'] = completed_files/elapsed_time if elapsed_time > 0 else 0
    save_dict_to_json(logreport, dest_dir, "logreport.json")