# COH3-image-extractor
## About
This repo stores scripts and instructions to extract images from COH3 files.

## Instructions

### Prerequisites
Install Python 3.X (the script was created and tested with 3.8)
Install requirements using:
```
 pip install -r requirements.txt
```

### Get the RRTEX files using Essence editor
* Open `EssenceEditor.exe` located in your Company of Heroes 3 folder
* In Essence editor, Open {your_coh_folder}\Company of Heroes 3\anvil\archives\UI.sga
* Right click the folder in Essence editor -> Export and choose location folder where to export RRTEX files
* You should have your *.RRTEX UI files exported


### Running the script
1. Execute `python scripts/main.py --src S:\coh3\ui` from the root of the repo

**Command-line Parameters:**
- `--src` Path to the folder with RRTEX files
- `--format` Output file format. Supported formats:
  - `tga` (default) - Highest quality, uncompressed
  - `png` - Lossless compression with transparency support
  - `webp` - Modern format with excellent compression and transparency support
- `--dst` or `--destination` Destination directory for output files (default: `export`)
- `--flatten` The output files will be in the same folder. Default is false, it will respect the folder structure of the source files.
If you flatten the folders. It's possible that files with the same name will be overwritten.
- `--threads` Number of worker threads for parallel processing. Default is auto-detected based on CPU cores.

**Usage Examples:**
```bash
# Basic usage with default settings (TGA format, export/ directory)
python scripts/main.py --src S:\coh3\ui

# Convert to PNG format
python scripts/main.py --src S:\coh3\ui --format png

# Convert to WebP format with custom destination
python scripts/main.py --src S:\coh3\ui --format webp --dst my_images

# Full example with all options
python scripts/main.py --src S:\coh3\ui --format webp --dst output --flatten --threads 8
```

2. Exported images will be in the specified destination folder (default: `export/`), mirroring the folder structure of `src_dir`
3. Check the `logreport.json` in the destination folder for details about conversion results.

**Format Comparison:**
- **TGA**: Uncompressed, highest quality, largest file size. Best for archival or when file size is not a concern.
- **PNG**: Lossless compression, good quality, moderate file size. Good balance between quality and size.
- **WebP**: Modern format with excellent compression, smallest file size while maintaining high quality. Recommended for web use or when storage space is limited.

**Performance Notes:**
- The script uses multithreading to process files in parallel, significantly improving performance on multi-core systems
- Thread count automatically defaults to the number of CPU cores detected
- Processing time and throughput statistics are included in the log report
- WebP conversion uses 85% quality setting for optimal balance between file size and visual quality


## Extracting map images
- In Essence editor open file "ScenariosMP.sga"
- You fill see all the maps
- Open the map folder and look for the .rtx file
- Open the image and do export

https://www.alecjacobson.com/weblog/?p=2064


## Known bugs
* there are some files (39/4479) we cannot convert at the moment. Ongoing investigation.


### Contributing
Original scripts and rrtex converter to tga by @rempAut ❤️  
Feel free to open issues and PRs.
