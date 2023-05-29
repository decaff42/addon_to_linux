#!/usr/bin/env python

"""addon_to_linux.py: Converts ysflight addons to lowercase paths."""

__author__      = "Decaff_42"
__copyright__   = "Copyright 2021, Decaff_42"
__license__     = "CC BY-NC-SA"
__version__     = "1.3.0"
__maintainer__  = "Decaff_42"
__status__      = "Production"
__date__        = "30 May 2021"

"""
Instructions:
    (1) Place this file in the directory which needs filenames, paths and
    ysflight .dat and .dnm internally defined paths formatted as lowercase.

    (2) Run this script.

This script will perform the following actions:
 (1) Convert all folders and files in directory to lowercase names
 (2) Convert all paths in .lst file to lower case
 (3) Convert all instrument panel and weapon skin paths in dat files to
     lower case
 (4) Convert all paths to external .srf files found in dnm files to lowercase
 (5) Detect issues with lst files having spaces.


Tested with:
 - Python 3.7.3 on Mac OS.
 - Python 3.8.1 on Windows 10
 - Python 2.7 & 3 on Linux

Version History
1.0.0 - Initial Release

1.0.1 - Fixed issue with LST file processing not swapping \ to / in filepaths.
1.0.2 - Fixed issue with scenery lst files throwing errors for the map name
        at the beginning of each line not being a path.
1.1.0 - Added a check for spaces in the filepaths.
1.1.1 - Fixed typos.

1.2.0 - Fixed issue where LST files have "_user/" instead of " user/"

1.3.0 - Added .acp file capability
"""

# Import python modules
import os

# Define custom functions
def rename_all_files_or_folders(root, items):
    for name in items:
        try:
            # Store the original file name
            original_path = os.path.join(root, name)        

            # Make new path with a lower case name
            new_path = os.path.join(root, name.lower())

            # Replace space with underscore
            new_path_string = str(new_path)
            new_path_string.replace(" ", "_")
            new_path = os.path.normpath(new_path_string)
            
            # Perform the file rename
            os.rename(original_path, new_path)
            
        except OSError:
            print("ERROR")
            print("Cannot rename {}".format(name))
            print("Check permissions and try again.")

def process_dat_file(filepath):
    # Instrument panels and weapon skins can have paths
    raw_file = import_text_file(filepath)

    if len(raw_file) > 0:
        for row, line in enumerate(raw_file):
            if line.startswith("INSTPANL") and ".ist" in line:
                # Found an externally defined instrument panel file path.
                path = line[9:] 
                path = convert_string_path(path)
                raw_file[row] = " ".join([line[:8], path])
                
            elif line.startswith("WPNSHAPE") and "." in line:
                # Found an externally defined weapon mesh.
                if "FLYING" in line:
                    parts = line.split("FLYING")
                else:
                    parts = line.split("STATIC")

                path = parts[-1][1:]  # Should be a space at beginning of string
                path = convert_string_path(path)
                parts[-1] = " " + path  # Add space back to the path

                if "FLYING" in line:
                    raw_file[row] = "FLYING".join(parts)
                else:
                    raw_file[row] = "STATIC".join(parts)

        write_text_file(raw_file, filepath)
    

def convert_string_path(path):
    path = path.lower()
    if "\\" in path:
        path = path.replace("\\", "/")
        
    if " " in path:
        path = path.replace(" ", "_")
    return path
        

def process_dnm_file(filepath):
    raw_file = import_text_file(filepath)

    if len(raw_file) > 0:
        for row, line in enumerate(raw_file):
            if ("/" in line or "\\" in line) and line.startswith("FIL"):
                path = line[4:]
                path = convert_string_path(path)

                raw_file[row] = "FIL " + path

        write_text_file(raw_file, filepath)
    

def process_lst_file(filepath):
    raw_file = import_text_file(filepath)

    if len(raw_file) > 0:
        # Scenery LST files need to be handled differenetly because we should
        # expect the first entry in each line to NOT be a path.
        lst_file_name = os.path.basename(filepath)
        if lst_file_name.startswith("sce"):
            is_scenery = True
        else:
            is_scenery = False

        # Convert each line of text to lower case
        for row, line in enumerate(raw_file):
            raw_file[row] = convert_string_path(line)

            # Version 1.2.0 fix to check for the _user issue caused by
            # convert_string_path function.
            if "_user" in raw_file[row]:
                raw_file[row] = raw_file[row].replace("_user", " user")

        # Check the filepaths in the lst line for completness
        for row, line in enumerate(raw_file):
            if len(line) > 20:  # Don't process empty lines
                parts = line.split(" ")
                for element, path in enumerate(parts):
                    if len(path) > 2:
                        # Path must be greater than 2 in order to account for
                        # the method of defining placeholders for files that
                        # should be in that position but are not included.
                        
                        # Some paths may be multiple spaces at trailing end of
                        # the lst file line. Ignore paths with zero length.
                        if is_scenery == True and element == 0:
                            # Ignore this line from the analysis
                            continue
                        elif "." not in path[-6:]:
                            # Need to account for " in the end of scenery paths.
                            print("Error in LST File Detected!")
                            print("Potential space in {}".format(lst_file_name))
                            print("Found in line {}".format(row + 1))

        write_text_file(raw_file, filepath)

def process_acp(filepath):
    raw_file = import_text_file(filepath)

    for i in range(0,4):
        raw_file[i] = convert_string_path(raw_file[i])

    write_text_file(raw_file, filepath)
    

def import_text_file(filepath):
    data = list()
    try:
        with open(filepath, "r") as txt_file:
            data = txt_file.readlines()
    except UnicodeDecodeError:
        non_unicode_text_alert(filepath)

    # Strip \n from rows
    for row, line in enumerate(data):
        if line.endswith("\n"):
            data[row] = line[:-1]
    return data        


def write_text_file(data, filepath):
    with open(filepath, 'w') as txt_file:
        for line in data:
            if "\n" not in line:
                txt_file.write(line + "\n")
            else:
                txt_file.write(line)


def non_unicode_text_alert(filepath):
    cwd = os.getcwd()
    rel_path = os.path.relpath(filepath, start=cwd)

    print("Unable to process {}".format(rel_path))
    print(" Check for non-unicode text in this file.")


####################################################################
#                                                                  #
#                       Script Begins Here                         #
#                                                                  #
####################################################################

                
# Initialize variables
cwd = os.getcwd()  # This is the directory that will be worked on.

# Rename all files to be lowercase and scrape out files that need to be handled
for root, dirs, files in os.walk(cwd, topdown=False):
    rename_all_files_or_folders(root, dirs)  # rename folders first
    rename_all_files_or_folders(root, files)

# Find all files to process now that the paths are renamed
for root, dirs, files in os.walk(cwd, topdown=False):
    for file in files:
        if file.endswith(".dat"):
            process_dat_file(os.path.join(root,file))
        elif file.endswith(".dnm"):
            process_dnm_file(os.path.join(root,file))
        elif file.endswith(".lst"):
            process_lst_file(os.path.join(root,file))
        elif file.endswith(".acp"):
            process_acp(os.path.join(root,file))
            



