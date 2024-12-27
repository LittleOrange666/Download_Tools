import codecs
import os
import subprocess
import glob
from PIL import Image

os.chdir(os.path.dirname(__file__))
with open("book_dictionary", encoding="utf8") as f:
    root = f.read()
import win32api
import win32con
import json
import time

ini_str = '''
[.ShellClassInfo]\r\n
IconResource=icon.ico,0\r\n
[ViewState]\r\n
Mode=\r\n
Vid=\r\n
FolderType=Pictures\r\n
'''
Any2Ico_path = 'Quick_Any2Ico.exe'
ext = ["jpg", "jpeg", "png", "gif", "icns", "ico", "webp"]
datf = "dat.json"

if __name__ == "__main__":
    root = root.strip('"').strip("'")
    print('--->', root)
    with open(datf) as f:
        dat = json.load(f)
    ot = time.mktime(tuple(dat["time"]))
    et = time.mktime(tuple(dat["time"]))
    count = 0
    for parent, dirnames, filenames in os.walk(root):
        if not dirnames and os.path.getctime(parent) > ot:
            count += 1
            et = max(et, os.path.getctime(parent))
    okc = 0
    for parent, dirnames, filenames in os.walk(root):
        if not dirnames and os.path.getctime(parent) > ot:
            print(parent)
            al = [p for p in os.listdir(parent) if p.split(".")[-1].lower() in ext]
            if len(al)==0:
                print(f"{parent} faild")
                continue
            first = min(al)
            use_webp = False
            if first.endswith("webp"):
                use_webp = True
                filename = f"{parent}\\{first}"
                save_name = filename.replace('webp', 'png')
                try:
                    im = Image.open(filename)
                    im.save('{}'.format(save_name), 'PNG')
                except:
                    print("webp convert Error!")
                    continue # skip error
                first = first[:-4]+"png"
            if os.path.exists('{0}/icon.ico'.format(parent)):
                os.remove('{0}/icon.ico'.format(parent))
            cmd = '"{0}" "-img={1}\\{2}" "-icon={1}\\icon.ico"'.format(Any2Ico_path, parent, first)
            subprocess.run(cmd)
            if use_webp:
                os.remove(f"{parent}\\{first}")
            win32api.SetFileAttributes('{0}/icon.ico'.format(parent), win32con.FILE_ATTRIBUTE_HIDDEN)
            desktop_ini = '{0}/desktop.ini'.format(parent)
            if os.path.exists(desktop_ini):
                os.remove(desktop_ini)
            f = codecs.open(desktop_ini, 'w', 'utf-8')
            f.write(ini_str)
            f.close()
            win32api.SetFileAttributes(desktop_ini, win32con.FILE_ATTRIBUTE_HIDDEN + win32con.FILE_ATTRIBUTE_SYSTEM)
            win32api.SetFileAttributes(parent, win32con.FILE_ATTRIBUTE_READONLY)
            okc += 1
            print(f"{okc}/{count}")
    dat["time"] = time.localtime(et);
    with open(datf, "w") as f:
        json.dump(dat, f)
