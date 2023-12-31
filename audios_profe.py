"""
This module contains a script to process and organize audio files from a
 specified source directory, convert opus/ogg audio files to mp3 format, and 
 organize them into sorted folders based on chat message topics. It performs the following steps:

1. Moves .zip files from the specified source directory to a local "profe" directory.
2. Extracts the contents of the .zip files into a ".dump" subdirectory within the "profe" directory.
3. Reads chat data from a specified file "_chat.txt" within the ".dump" directory.
4. Extracts relevant information from the chat data, including dates, times, senders, and messages.
5. Organizes the audio files based on message topics in the "profe/sorted" directory.
6. Converts opus/ogg audio files to mp3 format and removes the original opus/ogg files.

Module Components:
- paths.ZIP_SOURCE_DIR: The source directory containing .zip files to be processed.
- paths.PROFE_DIR: The main processing directory.
- paths.PROFE_SORTED_DIR: Directory where the sorted files will be organized.
- paths.DUMP_DIR: Directory where the contents of the .zip files are extracted.
- CHAT_FILE: The chat data file to be processed.
- PATTERN: Regular expression pattern to extract message details.
- FILENAME_PATTERN: Regular expression pattern to extract attached filenames.
- Matching Files: Finds opus and ogg files within the sorted directory for conversion.

Note: This module relies on the 'utils' package, specifically 'opus_to_mp3.py' 
and 'delete_dir.py' within the 'utils' directory.

Usage:
1. Run the script to process the .zip files, extract chat data, organize files, 
and convert opus/ogg files to mp3.
2. Ensure the required 'utils' modules are present in the same directory as this script.

Please ensure you have the necessary permissions and correct file paths before running this script.
"""

import shutil
import zipfile
import os
import re
import sys
import pickle
from utils.opus_to_mp3 import convert_opus_to_mp3
from colorama import Fore, Style
from consts import paths

CHAT_FILE = paths.DUMP_DIR / "_chat.txt"

# if os.path.exists(paths.DUMP_DIR):
#     delete_directory(paths.DUMP_DIR)

# Iterate through all files in the source directory with the specified file extension
if not list(paths.ZIP_SOURCE_DIR.glob("*profe.zip")):
    print(f"{Fore.RED}No files found in {paths.ZIP_SOURCE_DIR}{Style.RESET_ALL}")
    sys.exit()
for file_path in paths.ZIP_SOURCE_DIR.glob("*profe.zip"):
    print(f"Moving file '{file_path}' to '{paths.PROFE_DIR / file_path.name}'...")
    if not os.path.exists(paths.PROFE_DIR):
        os.makedirs(paths.PROFE_DIR)
    # Use the shutil.move() function to move the file from source to destination
    shutil.move(file_path, paths.PROFE_DIR / file_path.name)
    print(
        f"File '{file_path}' moved to '{paths.PROFE_DIR / file_path.name}' successfully."
    )

for zip_file in paths.PROFE_DIR.glob("*profe.zip"):
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(paths.DUMP_DIR)

# Read the file into a list of lines
if not CHAT_FILE.exists():
    print(f"{Fore.RED}File {CHAT_FILE} does not exist{Style.RESET_ALL}")
    sys.exit()

with open(CHAT_FILE, "r", encoding="UTF-8") as file:
    lines = file.readlines()

# Define the regular expression pattern to parse whatsapp messages
PATTERN = r"(\u200E)?\[(\d+/\d+/\d+), (\d+:\d+:\d+)\] ([\w\s]+): (.*)"

# The u200E utf character defines a system message that we use to parse attachments
FILENAME_PATTERN = r".*\u200E<attached: (.*)>"


if os.path.exists("pickle.pkl"):
    print("Loading pickle...")
    with open("pickle.pkl", "rb") as pkl_file:
        data_loaded = pickle.load(pkl_file)
        LAST_LINE = data_loaded["last_line"]
        temas = data_loaded["temas"]
else:
    temas = []
    LAST_LINE = 23

if LAST_LINE == len(lines):
    print(f"{Fore.YELLOW}No new lines to parse{Style.RESET_ALL}")
    sys.exit()
# Starting line is 23
for index, line in enumerate(lines[LAST_LINE:]):
    # Checks the regex for a message. It will match messages and attachments
    match = re.match(PATTERN, line)
    if match:
        tema = {}

        # If there is a match of the message it creates a new tema entry with the message. This will create new temas for messages that not precede a file. These will be cleaned after.
        char, date, time, sender, message = match.groups()
        if "omitted" not in message and "deleted" not in message and not char:
            tema["title"] = message.replace("/", "_")
            tema["files"] = []
            temas.append(tema)
            print(f"Appending {Fore.LIGHTYELLOW_EX}{tema['title']}{Style.RESET_ALL}")

        # Appends the files attached after a given message to a tema entry being the title the forementioned message
        if char and "omitted" not in message and "attached" in message:
            rematch = re.match(FILENAME_PATTERN, message.strip())
            if rematch:
                filename = rematch.groups()[0]
                audio_path = paths.DUMP_DIR / filename
                temas[-1]["files"].append(audio_path)

LAST_LINE = len(lines)


# Clean entries with empty file list
temas = [item for item in temas if item["files"]]

with open("pickle.pkl", "wb") as pkl_file:
    data_to_save = {"last_line": LAST_LINE, "temas": temas}
    # Example data saved
    """
    {'files': [PosixPath('profe/.dump/00000135-AUDIO-2023-10-04-17-00-22.opus'),
                        PosixPath('profe/.dump/00000136-AUDIO-2023-10-04-17-00-23.opus')],
    'title': 'Normativa PSX'}]}
    """
    pickle.dump(data_to_save, pkl_file)

for tema in temas:
    # If the folder title does not exist and the file list is not empty create the target folder
    if not os.path.exists(paths.PROFE_SORTED_DIR / tema["title"]) and tema["files"]:
        os.makedirs(paths.PROFE_SORTED_DIR / tema["title"])

    # For each of the files checks if the converted file exist
    # If the file does not exist is moved to the folder
    for file in tema["files"]:
        sorted_file_path = paths.PROFE_SORTED_DIR / tema["title"] / file.name
        if sorted_file_path.suffix in [".ogg", ".opus"]:
            sorted_file_path = (
                paths.PROFE_SORTED_DIR / tema["title"] / file.with_suffix(".wav").name
            )
        # If the converted file does not exist moves the original file
        if not sorted_file_path.exists():
            print(
                f"{Fore.LIGHTYELLOW_EX}Adding {file} to {paths.PROFE_SORTED_DIR / tema['title']} {Style.RESET_ALL}"
            )
            shutil.move(file, paths.PROFE_SORTED_DIR / tema["title"])


OPUS_EXTENSION = "*.opus"
OGG_EXTENSION = "*.ogg"
# Creates a list of all opus and ogg files in the sorted dir. Meaning if they
# are there they should be converted
matching_files = list(paths.PROFE_SORTED_DIR.rglob(OPUS_EXTENSION)) + list(
    paths.PROFE_SORTED_DIR.rglob(OGG_EXTENSION)
)

# Converts and deletes the old file
for file in matching_files:
    convert_opus_to_mp3(file)
    print(f"{Fore.GREEN}Converted {file}{Style.RESET_ALL}")
    file.unlink()
