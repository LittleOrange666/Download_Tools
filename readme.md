# nhentai download tools

A simple download tools for BitTorrent

## Installation

### Install the Python

Python version is not important for this program  
but Python 3.10.6 is suggested

### Install this repository

Using git:
```cmd
git clone https://github.com/LittleOrange666/Download_Tools.git
```
Or you can download zip file from github and unzip it.

### Install Python dependencies

```cmd
pip install -r requirements.txt
```

### Install qBittorrent

download it from [Download Page](https://www.qbittorrent.org/download) and install it  
Then, run any torrent file to setup the qBittorrent's default target folder  
and prevent it from always opening config windows.

### Install qBittorrent-cli

download it from [GitHub](https://github.com/fedarovich/qbittorrent-cli)  
you can choose a satisfy release from its release page  
Then, follow steps from [its directions](https://github.com/fedarovich/qbittorrent-cli/wiki/Getting-Started) to connect to qBittorrent

### setup target folder

create a file named "book_dictionary" without any filename extension  
and write full path of the book dictionary in it.  
It should equal to qBittorrent's default target folder.

Also, create a file named "torrent_dictionary" without any filename extension  
and write full path of the dictionary for downloaded torrent in it.

## Usage

You can send a POST request to "http://127.0.0.1:7777/download" to run a download request

request should contain the following parameters:  
name: filename of the torrent file, should be unique  
source: source page of the torrent, it will be save to show on the Book Reader  
target: direct link to download the torrent file  
cookie: cookie that can give access to the torrent file  
UserAgent: UserAgent that will use with cookie to get access to the torrent file

you may need a web-extendsion to send this request

following is a example for this

### web-extendsion for nhentai.net

First, you should have a nhentai account and login while browsing it.  
Install Tampermonkey on your browser, and create a new user script.

Then, replace it with content of "nhentai.js".

You should set up cookie at first time and whenever it is invalid.

First, login and pass the CAPTCHA test if it appear. Also, open the downloader.py.  
Second, open the developer tools, and open the "Network" Page.  
Third, find a GET request to "nhentai.net", scroll down to "request header" and find the "Cookie:".  
Copy everything in it, it may contains "csrftoken=", "sessionid=" and "cf_clearance=" three arguments.

Then, open the "Input" page from navbar, paste the cookie into the input field and click the "Save" button.

There are more functions to explore on your own.