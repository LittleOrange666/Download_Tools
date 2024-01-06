import os
import imghdr
import json
import subprocess

os.chdir(os.path.dirname(__file__))
with open("book_dictionary", encoding="utf8") as f:
    root = f.read()
with open("torrent_dictionary", encoding="utf8") as f:
    targetfolder = f.read()

if __name__ == "__main__":
    total = len(os.listdir(root))
    cnt = 0
    with open("codes.json", encoding="utf8") as f:
        codes = json.load(f)
    codes = {v: k for k, v in codes.items()}

    for folder in os.listdir(root):
        error = False
        all_files = []
        for file in os.listdir(os.path.join(root, folder)):
            if os.path.splitext(file)[0].isdigit():
                if imghdr.what(os.path.join(root, folder, file)) is None:
                    error = True
                all_files.append(int(os.path.splitext(file)[0]))
            if error:
                break
        if len(all_files) == 0 or max(all_files) > len(all_files):
            error = True
        if error:
            print("Error: "+folder)
            try:
                link = codes[folder]
            except KeyError:
                print("Error: idx not found")
                continue
            if link.endswith("/"):
                link = link[:-1]
            idx = link[link.rfind("/")+1:]
            print(f"{idx=}")
            filename = os.path.join(targetfolder, idx+".torrent")
            folder_name = os.path.join(root, folder)
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
