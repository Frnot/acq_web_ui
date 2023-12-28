import logging
from qobuz_dl.core import QobuzDL
from qobuz_dl.utils import create_and_return_dir
from dotenv import dotenv_values, set_key

logging.basicConfig(level=logging.INFO)

env = dotenv_values(".env")
email = env["email"]
password = env["password"]

qobuz = QobuzDL(folder_format="{year} - {album}",
                track_format="{tracknumber} - {tracktitle}",
                embed_art=True,
                overwrite=True)

qobuz.get_tokens() # get 'app_id' and 'secrets' attrs
qobuz.initialize_client(email, password, qobuz.app_id, qobuz.secrets)


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
