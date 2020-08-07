import re
import os
from . import extractors

HTML = 'html'
PDF = 'pdf'
DOCX = 'docx'
PPTX = 'pptx'
MSWORD = 'doc'

EXTRACTORS = {
    HTML: extractors.HtmlExtractor,
    PDF: extractors.PdfExtractor,
    DOCX: extractors.DocxExtractor,
    PPTX: extractors.PptxExtractor,
    MSWORD: extractors.MswordExtractor,
}


def _preprocess_text(text):
    # Remove NUL (0x00) characters
    text = text.replace('\x00', '')
    # Tabs and nbsps to space
    text = re.sub(r'(\t|&nbsp;)', ' ', text)
    # Single line breaks to spaces
    text = re.sub(r'(?<!\n)[ \t]*\n[ \t]*(?!\n)', ' ', text)
    # Multiple spaces to single
    text = re.sub(r' +', ' ', text)
    # More than 3 line breaks to just 3 line breaks
    text = re.sub(r'\n\s*\n\s*(\n\s*)+', '\n\n\n', text)
    return text.strip()


class Document:
    """
    A wrapper for document

    Helps extract any type of file
    """

    def __init__(self, doc, doc_type, params=None, extra_meta=None):
        self.doc_type = doc_type
        self.doc = doc
        self.params = params
        self.extra_meta = extra_meta or {}

    def extract(self):
        """
        Extracts text and images from the document

        Returns a tuple of text as string, images as list and page_count as int
        """
        extractor = EXTRACTORS.get(self.doc_type)
        text, images, page_count, word_count, file_size = None, [], 0, 0, None
        if hasattr(self.doc, 'seek') and hasattr(self.doc, 'fileno'):
            try:
                self.doc.seek(0, os.SEEK_SET)
                file_size = os.fstat(self.doc.fileno()).st_size
                self.doc.seek(0, os.SEEK_SET)
            except Exception:
                pass
        if extractor:
            text, images, page_count, extra_meta = extractor(self.doc, self.params).extract()

        if text:
            word_count = len(re.findall(r'\b\S+\b', text))

        if extra_meta:
            self.extra_meta.update(extra_meta)

        return self.doc_type, _preprocess_text(text), images, page_count, word_count, file_size, self.extra_meta
