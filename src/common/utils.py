import os
import secrets
import urllib
from mimetypes import guess_extension
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


def get_filename_from_url(url):
    return os.path.basename(urlparse(url).path)


def get_filename_from_base64(content):
    name = get_random_string(7)
    try:
        return name + guess_extension(content.split(';')[0].split(':')[1])
    except Exception:
        pass
    return name


def get_random_string(length, allowed_chars=(
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
)):
    """
    SOURCE: DJANGO
    Return a securely generated random string.
    The bit length of the returned value can be calculated with the formula:
        log_2(len(allowed_chars)^length)
    For example, with default `allowed_chars` (26+26+10), this gives:
      * length: 12, bit length =~ 71 bits
      * length: 22, bit length =~ 131 bits
    """
    return ''.join(secrets.choice(allowed_chars) for i in range(length))
