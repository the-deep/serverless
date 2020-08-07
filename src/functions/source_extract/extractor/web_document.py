import tempfile
import requests

from src.common.utils import DEFAULT_HEADERS, write_file
from src.functions.source_extract.web_info_extract.sources import get_web_info_extractor
from .document import (
    Document,
    HTML, PDF, DOCX, PPTX,
)


class WebDocument(Document):
    """
    Web documents can be html or pdf.
    Taks url Gives document and type
    """
    HTML_TYPES = ['text/html', 'text/plain']
    PDF_TYPES = ['application/pdf']
    DOCX_TYPES = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    PPTX_TYPES = ['application/vnd.openxmlformats-officedocument.presentationml.presentation']

    @classmethod
    def get_document(cls, url):
        doc_type = None
        doc = None

        content_type = None
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, stream=True, verify=False)
            response.raise_for_status()
            content_type = response.headers.get('content-type')
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
            return None, None

        if any(x in content_type for x in cls.HTML_TYPES):
            doc_type = HTML
            doc = response.text
        else:
            fp = tempfile.NamedTemporaryFile(dir='/tmp/', delete=False)
            write_file(response, fp)
            doc = fp

            if any(x in content_type for x in cls.PDF_TYPES):
                doc_type = PDF
            elif any(x in content_type for x in cls.DOCX_TYPES):
                doc_type = DOCX
            elif any(x in content_type for x in cls.PPTX_TYPES):
                doc_type = PPTX
        return doc_type, doc

    def __init__(self, url):
        doc_type, doc = self.get_document(url)
        web_extractor = get_web_info_extractor(url, content=doc, document_type=doc_type)
        doc = web_extractor.get_content()
        extra_meta = web_extractor.get_serialized_data()

        super().__init__(doc, doc_type, params={'url': url}, extra_meta=extra_meta)
