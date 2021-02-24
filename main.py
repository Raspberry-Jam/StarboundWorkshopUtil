import os
import shutil
import argparse
from typing import List, Tuple

printable = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
fs_printable = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-.()+@ '
working_dir = os.path.dirname(os.path.realpath(__file__))
parser = argparse.ArgumentParser(description="Copy and rename Starbound mod files from Steam workshop installation locations to the Starbound/mods folder.")


# Enumerate all mod files (exclusively named contents.pak) in workshop content folder
def enumerate_workshop_mods(workshop_dir: str) -> List[str]:
    mods = []
    for r, d, _ in os.walk(workshop_dir):  # Enumerate all directories and files under the workshop mods path (non-recursive)
        for directory in d:
            path = os.path.join(r, directory)  # Get the absolute path to the mod folder
            for __, ___, filenames in os.walk(path):
                for name in filenames:
                    if name.endswith('.pak'):  # Filter all files ending in '.pak'
                        mods.append(f'{path}{os.path.sep}{name}')  # Add absolute path of mod file
    return mods


# Get the name of the mod from the metadata of the file
def get_mod_name(file_path: str) -> str:
    index_match = b'INDEX'  # Byte array of the string 'INDEX' to match against file bytes
    name_match = b'\x04name'  # Byte array of string 'name' to match against subarray of file bytes
    name_offset = 0x00000000  # First instance of 'name' beginning from the offset in which the 'INDEX' match was made
    all_bytes = []  # All bytes from file
    metadata = []  # Bytes from file beginning from last instance of 'INDEX' to end of file
    name_bytes = []  # Bytes following the name_offset until a non-printable character is hit

    # Read in file as raw bytes
    with open(file_path, 'rb') as binfile:
        all_bytes = binfile.read()

    # Search from the end of file backwards to match for string 'INDEX'
    # and create a subarray beginning from that point up to end of file
    index_match_success = False
    for x in range(len(all_bytes), 0, -1):  # Iterate backwards over all_bytes
        if(all_bytes[x:(x+len(index_match))] == index_match):
            metadata = bytes(all_bytes[x:len(all_bytes)])
            index_match_success = True
            break

    del all_bytes

    if index_match_success is False:
        print("Metadata match not found!")
        exit(1)

    # Search from beginning of subarray to match for string 'name'
    # and return an offset position of match. OFFSET INCLUDES MATCH
    name_match_success = False
    for x in range(len(metadata)):
        if(metadata[x:(x+len(name_match))] == name_match):
            name_offset = x+7  # Name starts 7 bytes after beginning of name_match
            name_match_success = True

    if name_match_success is False:
        print("Name match not found in metadata! Was metadata matched incorrectly?")
        exit(1)

    # Beginning at the name_offset in metadata, append all bytes that are printable ascii
    # until a non-printable byte is hit
    for b in metadata[name_offset:len(metadata)]:
        if bytes([b]).decode('ascii') in printable:
            name_bytes.append(b)
        else:
            break

    del metadata

    # Return the ascii string represented by the name_bytes array
    return bytes(name_bytes).decode('ascii')


# Using the game's mods folder and provided paths for found workshop mods, get the mod names from the file metadata,
# translate the mod name into a filesystem friendly string, and copy the mod files into the game's mods folder,
# renaming the copies using the filesystem friendly names.
def copy_and_rename_mods(mod_dir: str, mod_paths: List[str]) -> None:
    for mod in mod_paths:
        raw_name = get_mod_name(mod)
        dest = ''
        for char in raw_name:
            if char in fs_printable:
                if char == ' ':
                    char = '_'
                dest += char
        dest = os.path.join(mod_dir, f'{dest}.pak')
        print(f'{mod} -> {dest}')
        shutil.copyfile(mod, dest)


def parse_args(parser: argparse.ArgumentParser) -> Tuple[str, str, str]:
    parser.add_argument('-g', '--gamedir', action='store', dest='gamedir', type=str, help='Installation directory of Starbound from Steam. This will seek workshop and mods folder automatically.')
    parser.add_argument('-m', '--moddir', action='store', dest='moddir', type=str, help='Destination mods folder of Starbound installation')
    parser.add_argument('-w', '--workshop', action='store', dest='workshop', type=str, help='Steam Workshop directory for Starbound mods, including Starbound ID (/.../workshop/content/211820/)')
    results = parser.parse_args()
    game_dir, mod_dir, workshop = (v if os.path.exists(str(v)) else None for _, v in results.__dict__.items())
    if game_dir is None:
        if mod_dir is None or workshop is None:
            print('Invalid argument usage! Workshop Utility requires either --gamedir or both --moddir and --workshop arguments. Use --help for more info.')
            exit(1)
    else:
        if not os.path.exists(f'{game_dir}{os.path.sep}..{os.path.sep}..{os.path.sep}workshop{os.path.sep}content{os.path.sep}211820'):
            print('Could not find a workshop folder in the expected location! Are you sure this is a valid Steam Starbound install directory? Use --help for more info.')
            exit(1)
        if not os.path.exists(f'{game_dir}{os.path.sep}mods'):
            print('Could not find a mods folder in the expected location! Are you sure this is a valid Starbound install directory? Use --help for more info.')
            exit(1)
    return (game_dir, mod_dir, workshop)


if __name__ == '__main__':
    game_dir, mod_dir, workshop_dir = parse_args(parser)

    if workshop_dir is None:
        if game_dir is None:
            print('This shouldn\'t be able to print. If so, both the game directory and the workshop directory are Null.')
            exit(1)
        else:
            workshop_dir = f'{game_dir}{os.path.sep}..{os.path.sep}..{os.path.sep}workshop{os.path.sep}content{os.path.sep}211820'

    if mod_dir is None:
        if game_dir is None:
            print('This shouldn\'t be able to print. If so, both the game directory and the workshop directory are Null.')
            exit(1)
        else:
            mod_dir = f'{game_dir}{os.path.sep}mods'

    paths = enumerate_workshop_mods(workshop_dir)
    copy_and_rename_mods(mod_dir, paths)
