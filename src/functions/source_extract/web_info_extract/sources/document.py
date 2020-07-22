from pdftitle import get_title_from_io as get_title_from_pdf

import tempfile
import requests

from src.common.utils import write_file, get_file_name_from_url
from .default import (
    DefaultWebInfoExtractor,
    HEADERS,
    PDF,
)


class DocumentWebInfoExtractor(DefaultWebInfoExtractor):
    def __init__(self, url, document_type):
        self.url = url
        self.readable = None
        self.page = None
        self.content = None
        self.type = document_type

        try:
            response = requests.get(url, headers=HEADERS, verify=False)
            self.content = response.content
        except requests.exceptions.RequestException:
            return

        fp = tempfile.NamedTemporaryFile(dir='/tmp/', delete=False)
        write_file(response, fp)
        self.content = fp

    def get_title(self):
        if self.type == PDF:
            try:
                return get_title_from_pdf(self.content)
            except Exception:
                return get_file_name_from_url(self.url)
        return super().get_title()

    def get_content(self):
        if self.content:
            self.content.seek(0)
        return self.content
