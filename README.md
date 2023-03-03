# coh3-image-extractor
## About
This repo stores scripts and instructions to extract images from COH3 files.

## Instructions

### Prerequisites
Install Python.

### Get the RRTEX files using Essence editor
* Open essence editor
* Open {your_coh_folder}\Company of Heroes 3\anvil\archives\UI.sga
* Right click the folder in Essence editor -> Export -> choose location
* You should have your *.RRTEX UI files exported

### The script
* open scripts/main.py
* modify this line - use path to the folder with RRTEX files.
    ```python
    src_dir = 'C:/coh-data/uisga/data/ui'
    ```

* run the script
* converted images are extracted to `export/`, mirroring the folder structure of `src_dir`
* check the `scripts\export\logreport.json` for details about conversion results.

## Known bugs
* there are some files (39/4479) we cannot convert at the moment. Ongoing investigation.
