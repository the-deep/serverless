from readability.readability import Document
from urllib.parse import urljoin

import html2text
import logging
import re
import requests
import tempfile
import base64

from deep_serverless.utils.common import (
    write_file,
    get_filename_from_url,
    get_filename_from_base64,
)

logger = logging.getLogger(__name__)


def _replace_with_newlines(element):
    text = ''
    for elem in element.recursiveChildGenerator():
        if isinstance(elem, str):
            text += elem.strip()
        elif elem.name == 'br':
            text += '\n\n'
    return text.strip()


def _get_plain_text(soup):
    plain_text = ''
    for line in soup.findAll('p'):
        line = _replace_with_newlines(line)
        plain_text += line
        plain_text += '\n\n'
    return plain_text.strip()


def process(doc, params):
    url = params['url']
    html_body = Document(doc)
    summary = html_body.summary()
    title = html_body.short_title()
    images = []

    for img in html_body.reverse_tags(html_body.html, 'img'):
        try:
            fp = tempfile.NamedTemporaryFile(dir='/tmp/')
            img_src = urljoin(url, img.get('src'))
            img_name = None
            if re.search(r'http[s]?://', img_src):
                r = requests.get(img_src, stream=True)
                img_name = get_filename_from_url(img_src)
                write_file(r, fp)
            else:
                img_meta, content = img_src.split(',')
                image = base64.b64decode(content)
                img_name = get_filename_from_base64(img_meta)
                fp.write(image)
            images.append((img_name, fp))
        except Exception:
            logger.error(
                'extractor.formats.html Image Collector Error!!',
                exc_info=True,
                extra={'data': {'url': url}},
            )

    html = '<h1>' + title + '</h1>' + summary
    html = '<p>{}</p>'.format(html)

    text = html2text.html2text(html)
    return text, images, 1, None
