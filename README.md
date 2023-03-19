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
- `--src` Path to the folder with RRTEX files
- `--format`  Output file format, default is tga which is the highest quality. You can switch to png. 
- `--flatten` The output files will be in the same folder. Default is false, it will respect the folder structure of the source files.
If you flatten the folders. It's possible that files with the same name will be overwritten.
- Full example `python scripts/main.py --src S:\coh3\ui --format png --flatten`

2. Exported images will be in `export/` folder, mirroring the folder structure of `src_dir`
3. Check the `scripts\export\logreport.json` for details about conversion results.


## Known bugs
* there are some files (39/4479) we cannot convert at the moment. Ongoing investigation.


### Contributing
Original scripts and rrtex converter to tga by @rempAut ❤️  
Feel free to open issues and PRs.