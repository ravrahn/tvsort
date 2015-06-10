#!/usr/local/env/tvsort/bin/python
import sys, os
import re, difflib, json, time
import unicodedata
import requests, sh
from bs4 import BeautifulSoup

# print to stdout (in case we're running in a terminal)
# and also to the log file
class logger(object):
    def __init__(self):
        self.stdout = sys.stdout
        self.log = open("/usr/local/log/tvsort.log", "a")

    def __del__(self):
        sys.stdout = self.stdout
        self.log.close()

    def write(self, data):
        self.stdout.write(data)
        self.log.write(data)

    def flush():
        self.stdout.flush()
        self.log.flush()

sys.stdout = logger()

TORRENT_DIR = "/mnt/storage/Torrents"
FILE_DIR = "/mnt/storage/TV"
FOLDER_LIST = os.listdir(FILE_DIR)
TORRENT_PATTERN = re.compile(r"^([a-zA-Z0-9\.]+)[\s\.][Ss]([0-9]{2})[Ee]([0-9]{2}).*\.([a-zA-Z0-9]+)$")

def api_url(series_name, season_number, episode_number):
    url = "http://services.tvrage.com/feeds/episodeinfo.php?show=%s&ep=%dx%d"
    url = url % (series_name, int(season_number), int(episode_number))
    return url

def get_file_name(torrent_id):
    torrent_info = json.loads(str(sh.gettorrentinfo(torrent_id)))
    # we assume the largest file (in size) is the important one
    largest_file = {"length": 0}
    for torrent_file in torrent_info["arguments"]["torrents"][0]["files"]:
        if torrent_file["length"] > largest_file["length"]:
            largest_file = torrent_file
    torrent_name = largest_file["name"]
    torrent_name = unicodedata.normalize('NFKD', torrent_name).encode('ascii','ignore')

    name_match = TORRENT_PATTERN.match(torrent_name)

    if name_match:
        series_name, season_number, episode_number, file_type = name_match.groups()
        series_name = re.sub(r"\.", r" ", series_name)
        series_name = re.sub(r"[0-9]", r"", series_name)
        episode_data = requests.get(api_url(series_name, season_number, episode_number))
        soup = BeautifulSoup(episode_data.text)
        episode_name = soup.episode.title.text

        folder = difflib.get_close_matches(series_name, FOLDER_LIST)[0]

        return "%s/%s/%d.%02d - %s.%s" % (FILE_DIR, folder, int(season_number), int(episode_number), episode_name, file_type)

# if there is an original file
def original_file_name(torrent_id):
    torrent_info = json.loads(str(sh.gettorrentinfo(torrent_id)))
    largest_file = {"length": 0}
    for torrent_file in torrent_info["arguments"]["torrents"][0]["files"]:
        if torrent_file["length"] > largest_file["length"]:
            largest_file = torrent_file
    return "%s/%s" % (TORRENT_DIR, largest_file["name"])

def get_series_name(torrent_id):
    torrent_info = json.loads(str(sh.gettorrentinfo(torrent_id)))
    # we assume the largest file (in size) is the important one
    # so this program will not work for whole-series torrents
    largest_file = {"length": 0}
    for torrent_file in torrent_info["arguments"]["torrents"][0]["files"]:
        if torrent_file["length"] > largest_file["length"]:
            largest_file = torrent_file
    torrent_name = largest_file["name"]
    torrent_name = unicodedata.normalize('NFKD', torrent_name).encode('ascii','ignore')

    name_match = TORRENT_PATTERN.match(torrent_name)

    if name_match is not None:
        series_name = name_match.groups()[0]
        series_name = re.sub(r"\.", r" ", series_name)
        series_name = re.sub(r"[0-9]", r"", series_name)

        return series_name
    else:
        return ""

print time.strftime("%a %Y/%m/%d %H:%M:%S")

torrents = json.loads(str(sh.gettorrents()))

torrent_count = 0

specific_torrent = ""
if len(sys.argv) > 1:
    specific_torrent = " ".join(sys.argv[1:])
    print "Series specified: %s" % specific_torrent

for torrent in torrents["arguments"]["torrents"]:
    torrent_count += 1

    torrent["name"] = unicodedata.normalize('NFKD', torrent["name"]).encode('ascii','ignore')

    series_name = get_series_name(torrent["id"])

    diff = difflib.SequenceMatcher(None, specific_torrent, series_name).ratio();

    if specific_torrent == "":
        diff = 0.0

    if torrent["leftUntilDone"] == 0 and (torrent["uploadRatio"] >= 2.0 or diff > 0.5):

        if diff > 0.5:
            print "Found matching completed torrent %s with ratio %.2f" % (torrent["name"], torrent["uploadRatio"])
        else:
            print "Found completed torrent %s with ratio %.2f" % (torrent["name"], torrent["uploadRatio"])
        og_name = original_file_name(torrent["id"])
        new_name = get_file_name(torrent["id"])

        print "Moving to %s" % (new_name)
        os.rename(og_name, new_name)

        print "Removing torrent"
        sh.removetorrent(torrent["id"])
    elif torrent["leftUntilDone"] != 0:
        print "Found incomplete torrent %s with ratio %.2f, ignoring" % (torrent["name"], torrent["uploadRatio"])
    elif diff < 0.5 and specific_torrent != "":
        print "Found non-matching torrent %s, ignoring" % torrent["name"]
    elif torrent["uploadRatio"] < 2.0:
        print "Found completed torrent %s with ratio %.2f, ignoring" % (torrent["name"], torrent["uploadRatio"])
    print

if torrent_count == 0:
    print "Found no torrents"
    print
