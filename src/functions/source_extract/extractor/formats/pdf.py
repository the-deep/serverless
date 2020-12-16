import logging
from io import BytesIO

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import (
    resolve1,
    PDFResourceManager,
    PDFPageInterpreter,
)
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

from pdftitle import get_title_from_io as get_title_from_pdf
from deep_serverless.utils.common import get_file_name_from_url


logger = logging.getLogger(__name__)


def process(doc, params):
    fp = doc
    fp.seek(0)

    with BytesIO() as retstr:
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        with TextConverter(
                rsrcmgr, retstr, codec='utf-8', laparams=laparams,
        ) as device:
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            maxpages = 0
            caching = True
            pagenos = set()
            for page in PDFPage.get_pages(
                    fp, pagenos, maxpages=maxpages,
                    caching=caching, check_extractable=True,
            ):
                try:
                    interpreter.process_page(page)
                except Exception:
                    logger.warning('PDF interpreter.process_page Error', exc_info=True)
            content = retstr.getvalue().decode()
    pages_count = get_pages_in_pdf(doc)
    title = get_title_in_pdf(doc, params and params.get('url'))
    return content, [], pages_count, {'title': title}


def get_pages_in_pdf(file):
    document = PDFDocument(PDFParser(file))
    return resolve1(document.catalog['Pages'])['Count']


def get_title_in_pdf(file, url):
    try:
        file.seek(0)
        return get_title_from_pdf(file)
    except Exception:
        return url and get_file_name_from_url(url)
