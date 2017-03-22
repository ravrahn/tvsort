#!/usr/local/bin/python3
import sys, os
import requests
from tvsortlib import *

# print to stdout (in case we're running in a terminal)
# and also to the log file
# sys.stdout = logger('/usr/local/log/sortfolder.log')

SORTED_DIR = '/mnt/storage/TV'
FOLDER_LIST = os.listdir(SORTED_DIR)

print(time.strftime('%a %Y/%m/%d %H:%M:%S'))

file_list = os.listdir(os.getcwd())
info_list = []


for f in file_list:
    f_info = torrent_info(f)
    f_info['orig_name'] = f
    if 'error' not in f_info:
        info_list.append(f_info)

for f in info_list:
    ep = episode_name(f['series'], f['season'], f['episode'])
    print('Found matching file {name}'.format(name=f['orig_name']))
    orig_name = '{dir}/{name}'.format(dir=os.getcwd(),name=f['orig_name'])
    new_name = sorted_path(f, FOLDER_LIST, SORTED_DIR)

    print('Moving to {name}'.format(name=new_name))
    os.rename(orig_name, new_name)
