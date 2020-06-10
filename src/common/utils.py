import os
import urllib
from urllib.parse import urlparse


def write_file(r, fp):
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            fp.write(chunk)
    return fp


def get_file_name_from_url(url):
    try:
        return urllib.parse.unquote(
            os.path.basename(
                urlparse(url).path
            ).split('.')[0]
        )
    except Exception:
        pass
