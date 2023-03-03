import os
import shutil

cwd = os.getcwd();
print(cwd)
# specify the source and destination directories
src_dir = 'C:/coh-data/uisga/data/ui'           # Extracted using EssenceEditor, open Company of Heroes 3\anvil\archives\UI.sga
dest_dir = 'C:/GIT/coh3-image-extractor/export' #save 

total_rtex_files = 0

# browse the source directory recursively
for dirpath, dirnames, filenames in os.walk(src_dir):
    # create a corresponding destination directory
    dest_subdir = dirpath.replace(src_dir, dest_dir, 1)
    os.makedirs(dest_subdir, exist_ok=True)
    
    # process all files in the current directory
    for file in filenames:
        
        file_extension = file.split('.')[1]
        file_name = file.split('.')[0]
        
        if file_extension == 'rrtex':
            total_rtex_files = total_rtex_files + 1
            src_file = os.path.join(dirpath, file)
            dest_file = os.path.join(dest_subdir, file_name+'.tga')
            #print(src_file)
            #print((dest_file))
        else:
            #print(f'skipping {file}')
            pass