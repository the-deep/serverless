#! /usr/bin/env python3

import xml.etree.ElementTree as ET
import tempfile
import zipfile
import re
import os
import random
import string
from subprocess import call
import logging

logger = logging.getLogger(__name__)

"""
Usage:
    text, images = process(doc, image_dir) -> images of image location
    text, images = process(doc) -> images for tempfile
"""

nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
         'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
         'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
         'wP': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',  # noqa
         }


def qn(tag):
    """
    Stands for 'qualified name', a utility function to turn a namespace
    prefixed tag name into a Clark-notation qualified tag name for lxml. For
    example, ``qn('p:cSld')`` returns ``'{http://schemas.../main}cSld'``.
    Source: https://github.com/python-openxml/python-docx/
    """
    prefix, tagroot = tag.split(':')
    uri = nsmap[prefix]
    return '{{{}}}{}'.format(uri, tagroot)


def xml2text(xml, pptx=False):
    """
    A string representing the textual content of this run, with content
    child elements like ``<w:tab/>`` translated to their Python
    equivalent.
    Adapted from: https://github.com/python-openxml/python-docx/
    """
    text = u''
    root = ET.fromstring(xml)
    if pptx is False:
        for child in root.iter():
            if child.tag == qn('w:t'):
                t_text = child.text
                text += t_text if t_text is not None else ''
            elif child.tag == qn('w:tab'):
                text += '\t'
            elif child.tag in (qn('w:br'), qn('w:cr')):
                text += '\n'
            elif child.tag == qn("w:p"):
                text += '\n\n'
    else:
        for child in root.iter():
            if child.tag == qn('a:t'):
                t_text = child.text
                text += t_text if t_text is not None else ''
            elif child.tag == qn('a:tab'):
                text += '\t'
            elif child.tag in (qn('a:br'), qn('a:cr')):
                text += '\n'
            elif child.tag in (qn("a:p"), qn("a:bodyPr"), qn("a:fld")):
                text += '\n\n'
    return text


def process(docx, params, pptx=False, img_dir=None):
    text = u''

    # unzip the docx in memory
    zipf = zipfile.ZipFile(docx)
    filelist = zipf.namelist()
    images = []
    page_count = 0

    # get header text
    # there can be 3 header files in the zip
    header_xmls = 'ppt/header[0-9]*.xml' if pptx else 'word/header[0-9]*.xml'
    for fname in filelist:
        if re.match(header_xmls, fname):
            text += xml2text(zipf.read(fname))

    # get main text
    doc_xml = 'ppt/slides/slide[0-9]*.xml' if pptx else 'word/document.xml'
    if pptx:
        for fname in filelist:
            if re.match(doc_xml, fname):
                text += xml2text(zipf.read(fname), pptx=pptx)
                # add page count if pptx
                page_count += 1
    else:
        text += xml2text(zipf.read(doc_xml))
        # get page count for docx
        page_count = get_pages_in_docx(docx)

    # get footer text
    # there can be 3 footer files in the zip
    footer_xmls = 'ppt/footer[0-9]*.xml' if pptx else 'word/footer[0-9]*.xml'
    for fname in filelist:
        if re.match(footer_xmls, fname):
            text += xml2text(zipf.read(fname))

    for fname in filelist:
        img_name = os.path.basename(fname)
        _, extension = os.path.splitext(img_name)
        if extension in [".jpg", ".jpeg", ".png", ".bmp"]:
            dst_f = tempfile.NamedTemporaryFile(dir='/tmp/')
            dst_f.write(zipf.read(fname))
            images.append((img_name, dst_f))

    zipf.close()

    return text.strip(), images, page_count, None


def pptx_process(docx, params, img_dir=None):
    return process(docx, params, pptx=True, img_dir=None)


def msword_process(doc, params, img_dir=None):
    tmp_filepath = '/tmp/{}'.format(
        ''.join(random.sample(string.ascii_lowercase, 10)) + '.doc'
    )

    with open(tmp_filepath, 'wb') as tmpdoc:
        tmpdoc.write(doc.read())
        tmpdoc.flush()

    # FIXME: THIS DOESN'T WORK
    call([
        'libreoffice', '--headless', '--convert-to', 'docx',
        tmp_filepath, '--outdir', '/tmp/',
    ])

    doc_filename = os.path.join(
        '/tmp/',
        re.sub(r'doc$', 'docx', os.path.basename(tmp_filepath))
    )

    response = process(doc_filename, params)

    # Clean up converted docx file
    call(['rm', '-f', doc_filename, tmp_filepath])
    return response


def get_pages_in_docx(file):
    with zipfile.ZipFile(file) as zipf:
        try:
            xml = zipf.read('docProps/app.xml')
            pages = ET.fromstring(xml).find('wP:Pages', nsmap)
            # pages could be False or None
            return int(pages.text) if pages is not None else 0
        except KeyError:
            logger.warning('Error reading page from docx {}'.format(
                file,
            ), exc_info=True)
            return 0
