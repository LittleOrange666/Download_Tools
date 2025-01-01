import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

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
    for _ in range(3):  # Retry up to 3 times
        try:
            res = requests.get(url, stream=True, timeout=10)  # Set timeout to 10 seconds
            if res.status_code != 200:
                print(f"Failed to download {url}")
                continue
            with open(path, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {url}: {e}")
            time.sleep(2)  # Wait for 2 seconds before retrying
    return False


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
    t0 = time.time() - 3600 * 24 * 7 * 10
    targets = [fn for fn in os.listdir(targetfolder) if fn.endswith(".torrent") and
               os.path.getmtime(os.path.join(targetfolder, fn)) > t0]
    for fn in tqdm(targets):
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

    def resolve(idx, name, fs):
        prefix, fn = get_link(idx, 1)

        def download_file(file):
            link = prefix + file.lstrip("0")
            path = os.path.join(root, name, file)
            return download(link, path)

        with ThreadPoolExecutor() as executor:
            results = list(tqdm(executor.map(download_file, fs), total=len(fs)))

        if all(results):
            os.system(f"qbt torrent delete {line[0]}")
        else:
            print("Failed to download")

    for line in dat:
        info = id_map[line[0]]
        idx = info[0][:-8]
        cnt = info[1]
        name = info[2]
        fs = info[4]
        os.makedirs(os.path.join(root, name), exist_ok=True)
        print(f"{idx} {cnt} {name}")
        resolve(idx, name, fs)
    os.system(r"python makeicon.py")


if __name__ == "__main__":
    main()
