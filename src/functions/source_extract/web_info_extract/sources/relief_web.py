import requests
import tldextract
import urllib.parse

from bs4 import BeautifulSoup
from readability.readability import Document
from urllib.parse import urlparse
from pdftitle import get_title_from_io as get_title_from_pdf


from src.functions.source_extract.extractor.document import (  # noqa: F401
    HTML, PDF, DOCX, PPTX, MSWORD,
)
from src.common.date_extractor import extract_date
from src.common.utils import get_file_name_from_url


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',  # noqa: E501
}


class DefaultWebInfoExtractor:
    def __init__(self, url, content=None, document_type='html'):
        self.url = url
        self.readable = None
        self.page = None
        self.content = content
        self.type = document_type
        self.reliefweb_url = 'https://reliefweb.int/'

        if self.content is None:
            try:
                response = requests.get(url, headers=HEADERS, verify=False)
                self.content = response.text
            except requests.exceptions.RequestException:
                return

        if self.type == 'html':
            html = self.content
            self.readable = Document(html)
            self.page = BeautifulSoup(html, 'lxml')

    def get_serialized_data(self):
        date = self.get_date()
        country = self.get_country()
        source_raw = self.get_source()
        author_raw = self.get_author()
        website = self.get_website()
        urls = self.get_urls()
        title = self.get_title()

        return {
            'source_raw': source_raw,
            'author_raw': author_raw,
            'title': title,
            'date': date,
            'country': country,
            'website': website,
            'urls': urls,
        }

    def get_title(self):
        # TODO: Legacy (Remove this)
        if self.type == PDF:
            try:
                return get_title_from_pdf(self.content)
            except Exception:
                return get_file_name_from_url(self.url)
        return self.readable and self.readable.short_title()

    def get_date(self):
        return extract_date(self.url, self.page)

    def get_country(self):
        if not self.page:
            return None
        country = self.page.select('.primary-country .country a')
        if country:
            return country[0].text.strip()

        country = self.page.select('.country')
        if country:
            return country[0].text.strip()

        return None

    def get_source(self):
        # TODO: Don't fetch here. cache when building function. NOTE: Lamba only allows write to /tmp/
        # https://github.com/john-kurkowski/tldextract#note-about-caching
        tldextract_extract = tldextract.TLDExtract(cache_file='/tmp/.tldextract-tld_set')
        return tldextract_extract(self.url).domain

    def get_author(self):
        if self.page:
            source = self.page.find('ul', {'class': 'rw-entity-meta__tag-value__list'})
            source_list = []
            if source:
                for src in source:
                    source_list.append(src.string)
            return source_list
        return []

    def get_website(self):
        return urlparse(self.url).netloc

    def get_content(self):
        return self.content

    def get_urls(self):
        if self.page:
            urls = self.page.find_all('section', {'class' : 'rw-attachment--report rw-attachment rw-file-list'})
            url_list = []
            if urls:
                for url in urls:
                    href_tag = url.find('a')
                    if href_tag:
                        url_list.append(self.reliefweb_url + urllib.parse.unquote(href_tag.get('href')))
            return url_list
        return []
