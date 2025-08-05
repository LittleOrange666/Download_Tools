import os
import imghdr
import json
import shutil
import subprocess

from torrentool.api import Torrent

os.chdir(os.path.dirname(__file__))
with open("book_dictionary", encoding="utf8") as f:
    root = f.read()
with open("torrent_dictionary", encoding="utf8") as f:
    targetfolder = f.read()

qbittorrent = r'"C:\Program Files\qBittorrent\qbittorrent.exe"'


def secure_filename(v):
    for ch in r'\/:*?"<>|':
        v = v.replace(ch, "_")
    return v


if __name__ == "__main__":
    btstat = subprocess.Popen('tasklist /FI "IMAGENAME eq qBittorrent.exe"',
                              stdout=subprocess.PIPE).communicate()[0].decode("cp950")
    if "exe" not in btstat:
        subprocess.Popen(qbittorrent)
        print("try opening Bittorrent")
    total = len(os.listdir(root))
    cnt = 0
    with open("codes.json", encoding="utf8") as f:
        codes = json.load(f)
    codes = {secure_filename(v): k for k, v in codes.items()}

    for folder in os.listdir(root):
        error = False
        all_files = []
        for file in os.listdir(os.path.join(root, folder)):
            if os.path.splitext(file)[0].isdigit():
                if imghdr.what(os.path.join(root, folder, file)) is None:
                    error = True
                    print("Broken image")
                all_files.append(file)
            if error:
                break
        if len(all_files) == 0:
            error = True
            print("Empty folder")
        folder_name = os.path.join(root, folder)
        try:
            link = codes[folder]
        except KeyError:
            print("Error: idx not found")
            try:
                shutil.rmtree(folder_name)
            except PermissionError:
                pass
            continue
        if link.endswith("/"):
            link = link[:-1]
        idx = link[link.rfind("/") + 1:]
        filename = os.path.join(targetfolder, idx + ".torrent")
        if not error:
            try:
                tor = Torrent.from_file(filename)
                exp = len(tor.files)
                if exp > len(all_files):
                    error = True
                    print("File missing, expected " + str(exp) + ", got " + str(len(all_files)))
            except:
                pass
        if error:
            print("Folder=" + folder)
            print(f"{idx=}")
            for file in os.listdir(folder_name):
                if not file.endswith(".ico"):
                    try:
                        os.remove(os.path.join(folder_name, file))
                    except PermissionError:
                        pass
            cmd = f"qbt torrent add file \"{filename}\""
            print(cmd)
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
            result = process.poll()
        cnt += 1
        print(f"{cnt}/{total}")
    os.system("python force_download.py")
