import os
import urllib
from urllib.parse import urlparse


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)' + \
    ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
}


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
