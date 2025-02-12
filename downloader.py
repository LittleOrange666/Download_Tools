# -*-coding:utf-8 -*-
import json
import os
import shutil
import subprocess
import time
import traceback
from multiprocessing import Lock

import requests
import win32api
import win32con

os.chdir(os.path.dirname(__file__))
with open("book_dictionary", encoding="utf8") as f:
    root = f.read()
with open("torrent_dictionary", encoding="utf8") as f:
    targetfolder = f.read()
from flask import Flask, request, Response
from flask_cors import cross_origin
from flask_apscheduler import APScheduler
from torrentool.api import Torrent
from torrentool.exceptions import BencodeDecodingError
from multiprocessing import Process, Queue, Manager
import force_download

lock = Lock()
app = Flask(__name__)
lasttime = -1
qbittorrent = r'"C:\Program Files\qBittorrent\qbittorrent.exe"'
book_reader = r"..\Book_Reader"
use_force_download = False
q = Queue()
hashes = []


def secure_filename(v):
    for ch in r'\/:*?"<>|':
        v = v.replace(ch, "_")
    return v


def thread_func(q: Queue):
    while True:
        if q.empty():
            time.sleep(3)
        else:
            a = q.get()
            os.system(f"qbt torrent delete {a}")


class Config(object):
    SCHEDULER_API_ENABLED = True


scheduler = APScheduler()


@scheduler.task('interval', id='do_job_1', seconds=10, misfire_grace_time=900)
def checker():
    global lasttime
    if lasttime != -1 and time.time() > 10 + lasttime:
        res = subprocess.run("qbt torrent list -f downloading -F list", stdout=subprocess.PIPE, text=True)
        out, err = res.stdout, res.stderr
        if err:
            print("Error: "+err)
            return
        if len(out) == 0:
            print("try make icon")
            os.system(r"python makeicon.py")
            lasttime = -1
            for h in hashes:
                q.put(h)
            hashes.clear()
        elif use_force_download:
            output = subprocess.check_output("qbt torrent list -F csv -f stalledDownloading", shell=True, text=True)
            ls = output.split("\n")
            if len(ls) <= 1:
                return
            h = ls[1].split(",")[0]
            with fd_info_lock:
                o = fd_info.get(h, None)
            if o is not None:
                print(f"force downloading {o[0]} {len(o[2])} {o[1]}")
                force_download.resolve(o[0], o[1], o[2], h)


@app.route('/download', methods=['POST'])
@cross_origin()
def download(trying=False):
    global lasttime
    name = request.form['name']
    url = request.form['target']
    source = request.form['source']
    filename = name + ".torrent"
    filename = os.path.join(targetfolder, filename)
    if request.form['cookie'] != "undefined":
        headers = {
            "cookie": request.form['cookie'],
            "User-Agent": request.form['UserAgent']
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            return Response(response="Cookie may be expired, please update it and try again", status=200)
        elif response.status_code == 500:
            print("Server Error, retrying...")
            time.sleep(2)
            return download(True)
        elif response.status_code != 200:
            return Response(response=f"link {url!r} get {response.status_code} response", status=200)
        try:
            open(filename, "wb").write(response.content)
        except PermissionError:
            print("Action failed, pass it")
            return Response(status=204)
        try:
            tor = Torrent.from_file(filename)
            fname = secure_filename(tor.name)
            with fd_info_lock:
                fd_info[tor.info_hash] = (name, fname, tuple(os.path.basename(o.name) for o in tor.files))
            folder_name = os.path.join(root, fname)
            with lock:
                if os.path.isdir(folder_name):
                    print("Removing old torrent")
                    win32api.SetFileAttributes(folder_name, win32con.FILE_ATTRIBUTE_DIRECTORY)
                    try:
                        shutil.rmtree(folder_name)
                    except PermissionError:
                        print("Remove failed, pass it")
                        return Response(status=204)
                    except FileNotFoundError:
                        pass
                os.makedirs(folder_name, exist_ok=True)
                with open("codes.json") as f:
                    obj = json.load(f)
                obj[source] = tor.name
                print(f"{source}: {tor.name}")
                with open("codes.json", "w") as f:
                    json.dump(obj, f, indent=2, sort_keys=True)
                with open(os.path.join(book_reader, "codes.json"), "w") as f:
                    json.dump(obj, f, indent=2, sort_keys=True)
                hashes.append(tor.info_hash)
        except BencodeDecodingError as e:
            traceback.print_exception(e)
            return Response(response="Fail to analyze torrent file", status=200)
        except json.decoder.JSONDecodeError:
            return Response(response="Some Error occured, this could be caused by requests with too short intervals",
                            status=200)
        except BaseException:
            raise
        cmd = f"qbt torrent add file \"{filename}\""
        print(cmd)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.wait()
        result = process.poll()
        if result:
            out = process.communicate()[1]
            res = "Unknown Error occurred"
            if "Unsupported Media Type" in out:
                res = "Cookie may be expired, please update it and try again"
            else:
                btstat0 = subprocess.check_output('tasklist /FI "IMAGENAME eq qBittorrent.exe"', text=True)
                if "exe" not in btstat0:
                    if trying:
                        res = "Cannot opening Bittorrent"
                    else:
                        subprocess.Popen(qbittorrent)
                        print("try opening Bittorrent")
                        time.sleep(3)
                        return download(True)
            print(out)
            return Response(response=res, status=200)
        # os.startfile(filename)
        lasttime = time.time()
        return Response(status=204)
    else:
        return Response(response="Cookie missing", status=200)


@app.route('/test', methods=['GET', 'POST'])
@cross_origin()
def get_test():
    return Response(status=200)


if __name__ == '__main__':
    fd_info = Manager().dict()
    fd_info_lock = Lock()
    btstat = subprocess.Popen('tasklist /FI "IMAGENAME eq qBittorrent.exe"',
                              stdout=subprocess.PIPE).communicate()[0].decode("cp950")
    if "exe" not in btstat:
        subprocess.Popen(qbittorrent)
        print("try opening Bittorrent")
    app.config.from_object(Config())
    scheduler.init_app(app)
    scheduler.start()
    Process(target=thread_func, args=(q,)).start()
    app.run(port=7777)
