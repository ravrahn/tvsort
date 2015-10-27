#!/usr/local/bin/python3
import sys, os
from tvsortlib import *

# print to stdout (in case we're running in a terminal)
# and also to the log file
sys.stdout = logger('/usr/local/log/tvsort.log')

TORRENT_DIR = '/mnt/storage/Torrents'
SORTED_DIR = '/mnt/storage/TV'
FOLDER_LIST = os.listdir(FILE_DIR)

print(time.strftime('%a %Y/%m/%d %H:%M:%S'))

torrents = json.loads(str(sh.gettorrents()))

torrent_count = 0

specific_torrent = ''
if len(sys.argv) > 1:
    specific_torrent = ' '.join(sys.argv[1:])
    print('Series specified: {}'.format(specific_torrent))

for torrent in torrents['arguments']['torrents']:
    torrent_count += 1

    name = original_path(torrent['id'])
    info = torrent_info(name)

    diff = difflib.SequenceMatcher(None, specific_torrent, info['series']).ratio();

    if specific_torrent == '':
        diff = 0.0

    if torrent['leftUntilDone'] == 0 and (torrent['uploadRatio'] >= 2.0 or diff > 0.5):

        if diff > 0.5:
            print('Found matching completed torrent {name} with ratio {ratio:.2f}'.format(name=torrent['name'], ratio=torrent['uploadRatio']))
        else:
            print('Found completed torrent {name} with ratio {ratio:.2f}'.format(name=torrent['name'], ratio=torrent['uploadRatio']))
        og_name = '{dir}/{name}'.format(dir=TORRENT_DIR, name=name)
        new_name = sorted_path(info, FOLDER_LIST, SORTED_DIR)

        print('Moving to {name}'.format(new_name))
        os.rename(og_name, new_name)

        print('Removing torrent')
        sh.removetorrent(torrent['id'])
    elif torrent['leftUntilDone'] != 0:
        print('Found incomplete torrent {name} with ratio {ratio:.2f}, ignoring'.format(name=torrent['name'], ratio=torrent['uploadRatio']))
    elif diff < 0.5 and specific_torrent != '':
        print('Found non-matching torrent {name}, ignoring'.format(name=torrent['name']))
    elif torrent['uploadRatio'] < 2.0:
        print('Found completed torrent {name} with ratio {ratio:.2f}, ignoring'.format(name=torrent['name'], ratio=torrent['uploadRatio']))
    print()

if torrent_count == 0:
    print('Found no torrents')
    print()
