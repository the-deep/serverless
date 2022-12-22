import urllib.parse


from .default import DefaultWebInfoExtractor


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',  # noqa: E501
}


class ReliefwebExtractor(DefaultWebInfoExtractor):
    def get_authors(self):
        authors = []
        if self.page:
            source = self.page.find(
                'ul',
                {'class': 'rw-entity-meta__tag-value__list'}
            ) or []
            for src in source:
                authors.append(src.string)
        return authors

    def get_pdf_urls(self):
        if self.page:
            urls = self.page.find_all(
                'section',
                {'class': 'rw-attachment--report rw-attachment rw-file-list'}
            )
            url_list = []
            if urls:
                for url in urls:
                    href_tag = url.find('a')
                    if href_tag:
                        url_list.append(
                            urllib.parse.urljoin(
                                'https://reliefweb.int/',
                                urllib.parse.unquote(href_tag.get('href'))
                            )
                        )
            return url_list
        return []

    def get_country(self):
        if not self.page:
            return None
        country = self.page.select(
            '.rw-entity-meta__tag-value--primary_country'
            ' > ul:nth-child(1) > li:nth-child(1) > a:nth-child(1)'
        )
        if country:
            return country[0].text.strip()
