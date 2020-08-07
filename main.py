import os
import shutil
from config import Config
from typing import List

printable = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ '
fs_printable = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-.()+@ '
working_dir = os.path.dirname(os.path.realpath(__file__))
config = Config(f'{working_dir}{os.path.sep}config.json')


# Enumerate all mod files (exclusively named contents.pak) in workshop content folder based on game installation path
# This assumes that the game is installed in a standard steam library directory structure
def enumerate_workshop_mods(game_dir: str) -> List[str]:
    content_path = f'{game_dir}{os.path.sep}..{os.path.sep}..{os.path.sep}workshop{os.path.sep}content{os.path.sep}211820'
    mods = []
    for r, d, f in os.walk(content_path):
        for directory in d:
            path = os.path.join(r, directory)
            for rr, dd, ff in os.walk(path):
                for name in ff:
                    if name.endswith('.pak'):
                        mods.append(f'{path}{os.path.sep}{name}')
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


def print_all_mod_names(mod_paths: List[str]) -> None:
    for mod in mod_paths:
        mod_name = get_mod_name(mod)
        print(f'{mod_name}')


def copy_and_rename_mods(game_dir: str, mod_paths: List[str]) -> None:
    mod_dir = os.path.join(game_dir, "mods")
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


if __name__ == '__main__':
    paths = enumerate_workshop_mods(config.config['game_dir'])
    copy_and_rename_mods(config.config['game_dir'], paths)
