import requests

from src.common.utils import DEFAULT_HEADERS
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
    def get_document_type(cls, url):
        doc_type = HTML
        content_type = None

        try:
            r = requests.head(url, headers=DEFAULT_HEADERS, verify=False)
            content_type = r.headers.get('content-type')
        except requests.exceptions.RequestException:
            # If we can't get header, assume html and try to continue.
            pass

        if content_type and any(x not in content_type for x in cls.HTML_TYPES):
            if any(x in content_type for x in cls.PDF_TYPES):
                doc_type = PDF
            elif any(x in content_type for x in cls.DOCX_TYPES):
                doc_type = DOCX
            elif any(x in content_type for x in cls.PPTX_TYPES):
                doc_type = PPTX
        return doc_type

    def __init__(self, url):
        doc_type = self.get_document_type(url)
        web_extractor = get_web_info_extractor(url, document_type=doc_type)
        doc = web_extractor.get_content()
        extra_meta = web_extractor.get_serialized_data()

        super().__init__(doc, doc_type, params={'url': url}, extra_meta=extra_meta)
