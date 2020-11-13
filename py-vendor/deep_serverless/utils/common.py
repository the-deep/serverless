import os
import secrets
import urllib
from mimetypes import guess_extension
from urllib.parse import urlparse

try:
    from django.conf import settings as django_settings
except ImportError:
    pass


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)' + \
    ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
}


def setting(name, *args):
    """
    key, fallback value
    """
    default = None
    default_defined = False
    if len(args):
        default = args[0]
        default_defined = True

    if not os.environ.get('IN_LAMBDA', False):
        # Use django settings for non lambda (for core deep)
        # DEEP_SERVERLESS is a prefix
        if default_defined:
            return getattr(django_settings, f'DEEP_SERVERLESS_{name}', default)
        return getattr(django_settings, f'DEEP_SERVERLESS_{name}')
    # In labmda use environment variables directly
    if default_defined:
        return os.environ.get(name, default)
    return os.environ[name]


def write_file(r, fp):
    for chunk in r.iter_content(chunk_size=1024):
        if chunk:
            fp.write(chunk)
    return fp


# TODO: same as get_filename_from_url
# This should also return filename without extension
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
