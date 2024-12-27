import json
import os
import subprocess
import time

from torrentool.api import Torrent
from torrentool.exceptions import BencodeDecodingError
from tqdm import *
import requests

with open("torrent_dictionary", encoding="utf8") as f:
    targetfolder = f.read()
with open("book_dictionary", encoding="utf8") as f:
    root = f.read()

"""
Hash,Name,MagnetUri,Size,Progress,DownloadSpeed,UploadSpeed,Priority,ConnectedSeeds,TotalSeeds,ConnectedLeechers,TotalLeechers,Ratio,EstimatedTime,State,SequentialDownload,FirstLastPiecePrioritized,Category,SuperSeeding,ForceStart,SavePath,AddedOn,CompletionOn,CurrentTracker,DownloadLimit,UploadLimit,Downloaded,Uploaded,DownloadedInSession,UploadedInSession,IncompletedSize,CompletedSize,RatioLimit,LastSeenComplete,LastActivityTime,ActiveTime,AutomaticTorrentManagement,TotalSize,SeedingTime,ContentPath
"""


def download(url, path):
    res = requests.get(url, stream=True)
    if res.status_code != 200:
        print(f"Failed to download {url}")
        return False
    with open(path, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
        return True


def secure_filename(v):
    for ch in r'\/:*?"<>|':
        v = v.replace(ch, "_")
    return v


def get_link(idx, page):
    link = f"https://nhentai.net/g/{idx}/{page}/"
    res = requests.get(link)
    content = res.text
    i = content.find("galleries")
    i = content.rfind("https://", 0, i)
    j = content.find('"', i)
    link = content[i:j]
    print(link)
    i = link.rfind("/")
    prefix = link[:i + 1]
    fn = link[i + 1:]
    return prefix, fn


def main():
    id_map = {}
    for fn in tqdm(os.listdir(targetfolder)):
        if fn.endswith(".torrent"):
            try:
                t = Torrent.from_file(os.path.join(targetfolder, fn))
                fs = [os.path.basename(o.name) for o in t.files]
                id_map[t.info_hash] = [fn, len(t.files), secure_filename(t.name),
                                       os.path.getmtime(os.path.join(targetfolder, fn)), fs]
            except BencodeDecodingError:
                pass
    with open("id_map.json", "w") as f:
        json.dump(id_map, f, indent=4)
    cmd = "qbt torrent list -F csv -f stalledDownloading"
    output = subprocess.check_output(cmd, shell=True, text=True)
    # parse output as csv format
    lines = output.split("\n")[1:]
    dat = [line.split(",") for line in lines]
    dat = [line for line in dat if line[0] in id_map]
    dat.sort(key=lambda x: id_map[x[0]][3])
    for line in dat:
        info = id_map[line[0]]
        idx = info[0][:-8]
        cnt = info[1]
        name = info[2]
        fs = info[4]
        os.makedirs(os.path.join(root, name), exist_ok=True)
        print(f"{idx} {cnt} {name}")
        for i in range(3):
            time.sleep(1)
            if i > 0:
                print("Retry")
            prefix, fn = get_link(idx, 1)
            for file in tqdm(fs):
                link = prefix + file.lstrip("0")
                path = os.path.join(root, name, file)
                if not download(link, path):
                    break
            else:
                os.system(f"qbt torrent delete {line[0]}")
                break
            print("Failed to download")


if __name__ == "__main__":
    main()
