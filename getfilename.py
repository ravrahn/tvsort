#!/usr/local/bin/python3
import sys
from tvsortlib import *

def get_file_name(series_name, season_number, episode_number):
    name = episode_name(series_name, season_number, episode_number)

    path_structure = '{season}.{episode:02d} - {name}'

    format_args = {
        'season': int(season_number),
        'episode': int(episode_number),
        'name': name
    }

    return path_structure.format(**format_args)

print(get_file_name(sys.argv[1], sys.argv[2], sys.argv[3]))
