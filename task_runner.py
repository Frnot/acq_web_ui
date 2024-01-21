import queue
import os
from metadata import Album, Track
import re
import shutil
import logging
import threading
import time
import traceback
from pathvalidate import sanitize_filepath

from qobuz_downloader import download_url


working_dir = "stage"
dest_dir = "/vault/media/audio/Music"

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class Task_Runner:
    def __init__(self, msg_queue):
        global logger
        logger = logging.getLogger(__name__)
        logger.addFilter(self.log_handler)
        for key in logger.root.manager.loggerDict.keys():
            if "qobuz" in key:
                logging.getLogger(key).addFilter(self.log_handler)

        self.jobs = queue.Queue()
        self.msg_queue = msg_queue
        #asyncio.create_task(self.run())
        threading.Thread(target=self.run).start()

    def run(self):
        while True:
            if not self.jobs.empty():
                try:
                    process(self.jobs.get())
                except Exception:
                    logger.error(traceback.format_exc())
                    logger.error("")
            else:
                time.sleep(1)

    def log_handler(self, record):
        msgs = record.msg.split("\n")
        for msg in msgs:
            msg = ansi_escape.sub('', msg)
            self.msg_queue.put(msg)
            #return True



def process(url):
    logger.info(f"Processing {url}")

    # download album with qobuz
    try:
        local_path, attr = download_url(url)
        local_path = sanitize_filepath(local_path)
    except:
        logger.error(f"URL: {url} invalid.")
        return
    
    album = attr["album"]
    artist = attr["artist"]
    year = attr["year"]
    if "title" in attr:
        title = attr["title"]
    else:
        title = None

    logger.info(f"Sanitizing tags at path: {local_path}")
    if title:
        new_album_name = sanitize(local_path, title)
    else:
        new_album_name = sanitize(local_path)
    if new_album_name:
        logger.info(f"Santized album name: {new_album_name}")
        album = new_album_name

    remote_path = os.path.join(dest_dir,artist,f"{year} - {album}")

    logger.info(f"Moving files from temp directory to {dest_dir}")
    logger.info(f"({local_path} -> {remote_path}")
    shutil.move(local_path, remote_path)
    os.rmdir(os.path.dirname(local_path))


def sanitize(album_path, single_name=None):
    for file in os.scandir(album_path):
        file_path = os.path.join(os.getcwd(), file.path)
        track = Track(file_path)
        album = track.album

    if single_name:
        track.tracknumber = "01"

    if single_name:
        if not (new_album_name := clean(single_name, regex_list)):
            new_album_name = single_name
    else:
        new_album_name = clean(album.name, regex_list)

    for track in album.tracks:
        if new_album_name:
            track.album_name = new_album_name
            logger.info(f"{track.filepath} new album: {new_album_name}")

        if new_title := clean(track.title, regex_list):
            track.title = new_title
            logger.info(f"{track.filepath} new title: {new_title}")

        if "," in track.artists:
            track.artists = track.artists.split(", ")

        # save changes to disk
        track.write_tags()

        if new_title:
            new_filepath = os.path.join(os.path.dirname(track.filepath), track.generate_filename())
            os.rename(track.filepath, new_filepath)
            track.file_path = new_filepath

    # specify write album directory
    return new_album_name


regex_list = [
    re.compile(r"\s*[({\[]explicit[)}\]]", re.IGNORECASE),  # explicit
    re.compile(r"\s*[({\[]\s*\d*\s*re[-]*master[ed]*\s*\d*\s*[)}\]]", re.IGNORECASE),  # remastered
    re.compile(r"\s*[({\[]\s*album\s+version\s*[)}\]]", re.IGNORECASE),  # "album version"
    re.compile(r"\s*[({\[].*release\s*[)}\]]", re.IGNORECASE),  # "US Release"
    re.compile(r"\s*[({\[]original.*\s*[)}\]]", re.IGNORECASE),  # "Original"
    re.compile(r"\s*[({\[].*version\s*[)}\]]", re.IGNORECASE),  # "* Version"
]

        

def clean(string, regexes):
    hits = 0
    for regex in regexes:
        string, hit = regex.subn("", string)
        hits += hit
    return string.strip() if hits else None


if __name__ == "__main__":
    url = "https://play.qobuz.com/album/yeu5ww39b8pya"
    process(url)