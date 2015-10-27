#!/usr/local/bin/python3
import sys, os
import re, difflib, json, time
import requests, sh

class logger(object):
    ''' Replacement for stdout
        Prints to both stdout and a log file '''
    def __init__(self, log_path):
        self.stdout = sys.stdout
        self.log = open(log_path, "a")

    def __del__(self):
        sys.stdout = self.stdout
        self.log.close()

    def write(self, data):
        self.stdout.write(data)
        self.log.write(data)

    def flush():
        self.stdout.flush()
        self.log.flush()

TORRENT_PATTERN = re.compile(r'^([a-zA-Z0-9\._]+)[\s\.][Ss]([0-9]{2})[Ee]([0-9]{2}).*\.([a-zA-Z0-9]+)$')
ALT_TORRENT_PATTERN = re.compile(r'^([a-zA-Z0-9\._]+)[\s\.]([0-9]+)x([0-9]+).*\.([a-zA-Z0-9]+)$')
PUNCTUATION = { 0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22 }

def api_url(series_name, season_number, episode_number):
    ''' Given a show's name, and the episode, return the URL
        that will get episode info '''
    lookup_url = 'http://api.tvmaze.com/singlesearch/shows?q={series}'.format(series=series_name)
    show = json.loads(requests.get(lookup_url).text)
    url = 'http://api.tvmaze.com/shows/{id}/episodebynumber?season={season}&number={episode}'
    url = url.format(id=show['id'], season=season_number, episode=episode_number)
    return url

def original_path(torrent_id):
    ''' Given a torrent's Transmission ID,
        return the video file belonging to it '''
    torrent_info = json.loads(str(sh.gettorrentinfo(torrent_id)))
    # we assume the largest file (in size) is the video
    largest_file = { 'length': 0 }
    for torrent_file in torrent_info['arguments']['torrents'][0]['files']:
        if torrent_file['length'] > largest_file['length']:
            largest_file = torrent_file
    torrent_name = largest_file['name']
    return torrent_name

def torrent_info(torrent_name):
    ''' Extract info about a torrent from its name '''

    name_match = TORRENT_PATTERN.match(torrent_name)
    if not name_match:
        name_match = ALT_TORRENT_PATTERN.match(torrent_name)

    if name_match:
        series_name, season_number, episode_number, filetype = name_match.groups()
        series_name = re.sub(r'[\._]', r' ', series_name)
        series_name = re.sub(r'[0-9]', r'', series_name)
        results = {
            'series': series_name,
            'season': int(season_number),
            'episode': int(episode_number),
            'filetype': filetype
        }
        return results
    else:
        return { 'error': 'No match' }

def episode_name(series, season, episode_number):
    episode_url = api_url(series, season, episode_number)
    episode = json.loads(requests.get(episode_url).text)
    name = episode['name']

    return name

def sorted_path(torrent_info, folder_list, sorted_dir):
    ''' Given info about a torrent, return a path
        for it in line with the sorting system '''

    if 'error' not in torrent_info:
        episode = episode_name(torrent_info['series'], torrent_info['season'], torrent_info['episode'])

        folders = difflib.get_close_matches(torrent_info['series'], folder_list)

        if len(folders) == 0:
            folder = '{root}/{folder}'.format(root=sorted_dir, folder=torrent_info['series'])
            os.mkdir(folder)
        else:
            folder = '{root}/{folder}'.format(root=sorted_dir, folder=folders[0])

        path_structure = '{dir}/{season}.{episode:02d} - {name}.{filetype}'

        format_args = {
            'dir': folder,
            'season': int(torrent_info['season']),
            'episode': int(torrent_info['episode']),
            'name': episode,
            'filetype': torrent_info['filetype']
        }

        return path_structure.format(**format_args)
    else:
        return None



