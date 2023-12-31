import queue
import os
from metadata import Album, Track
import re
import asyncio
import justpy as jp
import shutil
import logging

from qobuz_downloader import download_url


logger = logging.getLogger(__name__)

working_dir = "stage"
dest_dir = "/vault/media/audio/Music"

class Task_Runner:
    def __init__(self):
        self.jobs = queue.Queue()
        asyncio.create_task(self.run())

    async def run(self):
        while True:
            if not self.jobs.empty():
                await process(*self.jobs.get())
            else:
                await asyncio.sleep(1)


# TODO: run qobuz-dl in a separate thread, have its logger push to a queue
# Have main thread aync pull from queue and display


async def process(url, web_page):

    #web_page.logs.add_component(jp.P(text=f'Printing {url} idx: {_}'), 0)
    #await web_page.logs.update()
    logger.info(f"Processing {url}")

    # download album with qobuz
    local_path, artist, album, year = download_url(url)
    print(local_path)

    new_album_name = sanitize(local_path)
    if new_album_name:
        album = new_album_name

    remote_path = os.path.join(dest_dir,artist,f"{year} - {album}")
    #shutil.move(local_path, remote_path)


def sanitize(album_path):
    for file in os.scandir(album_path):
        file_path = os.path.join(os.getcwd(), file.path)
        track = Track(file_path)
        album = track.album

    new_album_name = clean(album.name, regex_list)

    for track in album.tracks:
        if new_album_name:
            track.album = new_album_name

        if new_title := clean(track.title, regex_list):
            track.title = new_title

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