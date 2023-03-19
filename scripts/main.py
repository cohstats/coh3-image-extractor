import os
import json
import argparse
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert rrtex files to tga.')
    parser.add_argument('--src', metavar='--src', type=str, help='path to source directory')
    parser.add_argument('--format', metavar='format', type=str, default='tga', help='image output format (default: tga)')
    parser.add_argument('--flatten', dest='flatten', action='store_true', help='description of parameter (default: False)')
    parser.set_defaults(flatten=False)

    args = parser.parse_args()

    src_dir = args.src
    image_format = args.format
    flatten = args.flatten

    dest_dir = os.path.join(os.getcwd(), 'export/')

    print("Starting image extraction ...")
    print(f"Source directory: {src_dir}")
    print(f"Destination directory: {dest_dir}")

    stats = {}
    stats['rrtex'] = 0
    stats['converted'] = 0
    stats['failed'] = 0
    stats['skipped'] = 0

    details = {}
    details['failed'] = []
    details['skipped'] = []

    # browse the source directory recursively
    for dirpath, dirnames, filenames in os.walk(src_dir):
        # create a corresponding destination directory
        dest_subdir = dirpath.replace(src_dir, dest_dir, 1)
        os.makedirs(dest_subdir, exist_ok=True)

        # process all files in the current directory
        for file in filenames:
            src_file = os.path.join(dirpath, file)
            file_extension = file.split('.')[1]
            file_name = file.split('.')[0]
            print(f"processing {file_name}")
            # if rrtex, try to convert
            if file_extension == 'rrtex':
                stats['rrtex'] += 1
                dest_file = os.path.join(dest_subdir, file_name + '.' + image_format)
                if flatten:
                   dest_file = os.path.join(dest_dir, file_name + '.' + image_format)
                try:
                    convert_rrtex(src_file,dest_file)
                    stats['converted'] += 1
                except Exception as e:
                    stats['failed'] += 1
                    log_details(details['failed'],src_file, str(e))
                else:
                    stats['skipped'] += 1
                    log_details(details['skipped'],src_file, "Not RRTEX file." )

print(f"{stats}")

logreport = {}
logreport['stats'] = stats
logreport['details'] = details
save_dict_to_json(logreport, dest_dir, "logreport.json" )