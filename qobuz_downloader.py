import logging
from qobuz_dl.core import QobuzDL
from qobuz_dl.utils import create_and_return_dir, get_url_info
from qobuz_dl.exceptions import AuthenticationError, IneligibleError
from dotenv import dotenv_values, set_key
import os

offline_testing = False


env = dotenv_values(".env")
email = env["email"]
password = env["password"]

authenticated = False

qobuz = QobuzDL(directory="stage",
                folder_format="{artist}/{year} - {album}",
                track_format="{tracknumber} - {tracktitle}",
                embed_art=True,
                cleanup_cover=True)

qobuz.get_tokens() # get 'app_id' and 'secrets' attrs
#qobuz.initialize_client(email, password, qobuz.app_id, qobuz.secrets)
  


def authenticate(email=email, password=password):
    if offline_testing:
        if email=="valid" and password=="valid":
            return True
        else:
            return False
    
    global authenticated
    try:
        qobuz.initialize_client(email, password, qobuz.app_id, qobuz.secrets)
        authenticated = True
    except (AuthenticationError, IneligibleError) as e:
        pass
    return authenticated


def check_auth(func):
    def wrapper(*args, **kwargs):
        if not authenticated:
            #if authenticate():
            #    return func(*args, **kwargs)
            #else:
                raise Exception("Error: unauthorized. Try calling authenticate() with valid credentials")
        else:
            return func(*args, **kwargs)
    return wrapper
    

@check_auth
def download_url(url):
    """Downloads track/album at provided URL to local directory"""
    qobuz.handle_url(url)
    url_type, item_id = get_url_info(url)

    if url_type == "track":
        meta = qobuz.client.get_track_meta(item_id)
        attr = {
            "artist": meta["performer"]["name"],
            "album": meta["album"]["title"],
            "year": meta["release_date_original"].split("-")[0],
            "title" : meta["title"],
        }
        path = os.path.join(qobuz.directory, os.path.normpath(qobuz.folder_format.format(**attr)))

    else: # album
        meta = qobuz.client.get_album_meta(item_id)
        attr = {
            "artist": meta["artist"]["name"],
            "album": meta["title"],
            "year": meta["release_date_original"].split("-")[0],
        }
        path = os.path.join(qobuz.directory, os.path.normpath(qobuz.folder_format.format(**attr)))

    return (path, attr)


@check_auth
def download_album(album_name, artist, dl_path):
    query = f"{artist} - {album_name}"
    search_results = qobuz.search_by_type(query, "album", limit=10)
    print(f"{search_results=}")

    url = None
    potential_results = []
    for result in search_results:
        trimmed_result = re.search(r"(.*) - \d\d:\d\d:\d\d", result['text']).group(1)
        if (match_ratio := fuzz.ratio(trimmed_result.lower(), query.lower())) > 80:
            potential_results.append((match_ratio, result['url']))
    
    if not potential_results:
        print(f"Didn't find a good match for query '{query}'")
        return False
    
    max = 0
    best_url = ""
    for score,url in potential_results:
        if score > max:
            max = score
            best_url = url

    qobuz.directory = create_and_return_dir(dl_path)
    qobuz.handle_url(best_url)
    return True
