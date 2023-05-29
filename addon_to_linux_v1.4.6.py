#!/usr/bin/env python

"""addon_to_linux.py: Converts ysflight addons to lowercase paths."""

__author__      = "Decaff_42"
__copyright__   = "Copyright 2021, Decaff_42"
__license__     = "CC BY-NC-SA"
__version__     = "1.4.6"
__maintainer__  = "Decaff_42"
__status__      = "Production"
__date__        = "29 May 2023"

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
 (5) Detect issues with lst files having spaces where they should not.


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

1.4.0 - Fixed issue with corrupting lst files due to unwanted spaces
      - Added instructions for how to handle unicode detection
1.4.1 - Fixed issue with underscore between scenery name and fld path.
        Re-did the lst file space replacement to evaluate each space individually.
1.4.2 - Adds DAT ACP definition capability to existing DAT file processing.
      - Adds basic .fld file capability.
1.4.3 - Updates .fld file processing to ignore internal PCK elements from the path
        updating for the FIL lines.
1.4.4 - Fixed issue with DAT CARRIER (acp) paths losing the first character in the path
1.4.5 - Updated DNM processing to ignore internally-defined SURFs
1.4.6 - Fixed DNM parsing issue with invalid variable name in loop
"""

# Import python modules
import os
import re


# Define custom functions
def rename_all_files_or_folders(root, items):
    """Loops through all the filenames or folders in a directory and renames them to lowercase.
    
    inputs:
    root (str): os.path like folder to operate in
    items (list): list of string file or foldernames in the root directory.
    """
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
    """open and process a .dat file and convert all paths to lower case. 
    
    Only instrument panels, weapon skins can have filepaths defined in aircraft .dat files, however
    carrier ground objects will have filepaths in them.
    
    Note: Do not need to check if the input is a dat file since this function is only called when
          that check has been passed.
    
    input:
    filepath (str): os.path-like string to where a dat file is at
    """
    
    raw_file = import_text_file(filepath)

    if len(raw_file) > 0:
        for row, line in enumerate(raw_file):
            if line.startswith("INSTPANL") and ".ist" in line:
                # Found an externally defined instrument panel file path.
                if "#" in line:
                    line = line.split('#')[0]
                path = line[9:] 
                path = convert_string_path(path)
                raw_file[row] = " ".join([line[:8], path])
                
            elif line.startswith("WPNSHAPE") and (".srf" in line.lower() or ".dnm" in line.lower()):
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

            elif line.startswith("CARRIER") and "." in line:
                # version 1.4.2 update
                path = line.split()[-1] 
                path = convert_string_path(path)
                raw_file[row] = " ".join([line[:8], path])

        write_text_file(raw_file, filepath)
    

def convert_string_path(path):
    """convert a string from a YSFlight file into a lowercase path.
    
    inputs:
    path (str): os.path-like string from the YSFlight File
    """
    
    filetypes = ["srf", "dnm", "acp", "dat", "fld", "stp", "yfs"]
    locations = ["user", "aircraft", "ground", "scenery"]
    
    path = path.lower()
    if "\\" in path:
        path = path.replace("\\", "/") # This format is required for MacOS
        
    if " " in path:
        # Version 1.4.1 update to better identify spaces that are allowed,
        # rather than brute force replace all and then try to undo the
        # problem later. Keep the undo functionality as that works, but
        # don't shoot ourselves in the foot to begin with.
        
        # Search for spaces that are allowed.
        # 1 - after a .filetype
        # 2 - before a location
        space_idxs = [m.start() for m in re.finditer(" ", path)]
        valid_spaces = list()
        for idx in space_idxs:
            # Evaluate each space individually
            valid_space = False

            # Test for valid condition 1, after a filetype.
            if idx > 3:
                for filetype in filetypes:
                    if path[:idx].endswith(filetype):
                        valid_space = True

            # Test for valid condition 2, before a location
            for location in locations:
                if path[idx + 1:].startswith(location):
                    valid_space = True
                
            valid_spaces.append(valid_space)

        # Replace each invalid space with an underscore
        for idx, validity in zip(space_idxs, valid_spaces):
            if validity is False:
                path = path[:idx] + "_" + path[idx + 1:]

                    
    # Version 1.4.0 fix to look for issues with acceptable spaces
    # being converted to underscores.
    
    for filetype in filetypes:
        search = filetype + "_"
        replace = filetype + " "
        if search in path:
            path = path.replace(search, replace)

    # Version 1.4.0 fix to replace the v1.2.0 fix with common locations for addons.
    for location in locations:
        search = "_" + location
        if search in path:
            start_idxs = [m.start() for m in re.finditer(search, path)]
            for idx in start_idxs:
                for filetype in filetypes:
                    new_search = filetype + search
                    new_replace = "{} {}".format(filetype, location)
                    if new_search in path:
                        path = path.replace(new_search, new_replace)
            
    return path
        

def process_dnm_file(filepath):
    """convert the paths inside a DNM file into lowercase paths to match the addon file structure 
    changes.
    
    Note: Do not need to check if this is a DNM file because this function is only called after that
          check is performed in the calling fucntion.
    
    inputs:
    filepath (str): os.path-like to where a dnm file is.
    """
    raw_file = import_text_file(filepath)
    
    if len(raw_file) > 0:
        # Identify internally defined elements.
        pck_names = list()
        for line in raw_file:
            if line.startswith("PCK"):
                # Unknown if spaces can exist in the PCK name, so we will make the name
                # extraction so it doesn't matter. We know that the length of the 
                parts = line.split()
                if len(parts) > 2:
                    num_length_characters = -1*(len(parts[-1]) + 2)
                    name = line[4:1 + num_length_characters]
                else:
                    name = parts[0]
                
                pck_names.append(name)

        # Process the SRF FIL lines.
        for row, line in enumerate(raw_file):
            if line.startswith("FIL"):
                path = line[4:]
                path = convert_string_path(path)

                raw_file[row] = "FIL " + path

        write_text_file(raw_file, filepath)
    

def process_lst_file(filepath):
    """convert all paths in a LST file into lowercase to match the addon file structure changes.
    
    Note: Do not need to check if this is a LST file because this function is only called after that
          check is performed in the calling fucntion.
    
    inputs:
    filepath (str): os.path-like to where a lst file is.
    """
    
    raw_file = import_text_file(filepath)

    if len(raw_file) > 0:
        # Scenery LST files need to be handled differently because we should
        # expect the first entry in each line to NOT be a path.
        lst_file_name = os.path.basename(filepath)
        if lst_file_name.startswith("sce"):
            is_scenery = True
        else:
            is_scenery = False

        # Convert each line of text to lower case
        for row, line in enumerate(raw_file):
            raw_file[row] = convert_string_path(line)

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
                            print("  Potential space in {}".format(lst_file_name))
                            print("  Found in line {}".format(row + 1))
                            print("  {}".format(path))

        write_text_file(raw_file, filepath)


def process_fld(filepath):
    """convert all paths in a FLD file into lowercase to match the addon file structure changes.
    
    Note: Do not need to check if this is a FLD file because this function is only called after that
          check is performed in the calling fucntion.
    
    inputs:
    filepath (str): os.path-like to where a fld file is.
    """
    raw_file = import_text_file(filepath)
    # Version 1.4.6 addtion - .srf files can be included in the FLD file.
    ftypes = [".fld", ".pc2", ".ter", ".srf"]  # These files can be externally defined in a FLD 

    # No need to overwrite PCK element names as these are custom defined in the FLD file and NOT external files
    pck_names = list()
    for line in raw_file:
        if line.startswith("PCK "):
            pck_names.append(line.split('"')[1])

    # Find all FIL lines that reference an external file, i.e. not
    # in the PCK list.
    for idx, line in enumerate(raw_file):
        if line.startswith("FIL") and "." in line:
            temp_line = line.lower()
            if any(substring in temp_line for substring in ftypes) is True:
                # Needs to work with .pc2, .fld, .ter files
                if '"' in line:
                    path = line.split('"')[1]
                else:
                    path = line[4:]

                if path not in pck_names:
                    path = convert_string_path(path)
                    raw_file[idx] = 'FIL "{}"'.format(path)

    write_text_file(raw_file, filepath)


def process_acp(filepath):
    """process the aircraft carrier properties file.
    
    inputs:
    filepath (str): os.path-like to where a acp file is.
    """
    raw_file = import_text_file(filepath)

    for i in range(0,4):
        raw_file[i] = convert_string_path(raw_file[i])

    write_text_file(raw_file, filepath)
    

def import_text_file(filepath):
    """Import a text file as a list of strings but without the newline character at the end.
    
    inputs:
    filepath (str): os.path-like to where a file to read in is located.
    """
    data = list()
    try:
        with open(filepath, "r", encoding="utf8") as txt_file:
            data = txt_file.readlines()
    except UnicodeDecodeError:
        non_unicode_text_alert(filepath)

    # Strip \n from rows
    for row, line in enumerate(data):
        if line.endswith("\n"):
            data[row] = line[:-1]
    return data        


def write_text_file(data, filepath):
    """write a modified YSFlight file to the specified location
    
    inputs:
    data (list): list of strings where each element is a complete row of the file.
    filepath (str): os.path-like to where the file should be written to.
    """
    
    with open(filepath, 'w') as txt_file:
        for line in data:
            if "\n" not in line:
                txt_file.write(line + "\n")
            else:
                txt_file.write(line)


def non_unicode_text_alert(filepath):
    """Perform error handling catch when a non-unicode element is in the text file. This is more 
    common in older addons from the Japaneese community, but can sneak in from anywhere.
    
    Use a relative path so that the user can start at the addon level and not have to dig through 
    unnecessary filepath elements for the absolute path to where the file is located.
    
    inputs:
    filepath (str): os.path-like to where the problem file is located.
    """
    
    cwd = os.getcwd()
    rel_path = os.path.relpath(filepath, start=cwd)

    print("Unable to process {}".format(rel_path))
    print("  Check for non-unicode text in this file and delete bad characters. Then re-run this code.")


####################################################################
#                                                                  #
#                       Script Begins Here                         #
#                                                                  #
####################################################################


print("Starting addon_to_linux version {}\n\n".format(__version__))

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
            process_dat_file(os.path.join(root, file))
        elif file.endswith(".dnm"):
            process_dnm_file(os.path.join(root, file))
        elif file.endswith(".lst"):
            process_lst_file(os.path.join(root, file))
        elif file.endswith(".acp"):
            process_acp(os.path.join(root, file))
        elif file.endswith(".fld"):
            process_fld(os.path.join(root, file))

print("\n\nComplete.")
            
