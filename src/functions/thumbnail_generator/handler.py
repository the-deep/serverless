import logging

from deep_serverless.utils import sentry  # noqa: F401
from deep_serverless.utils.common import unpack_binary
from deep_serverless.models.base import get_or_none
from deep_serverless.models.source_extract import Source
from deep_serverless.static import ExtractorStatic

logger = logging.getLogger(__name__)


def _get_thumbnail(source):
    from . import generator

    # TODO: ONLY UNPACK IF REQUIRED
    # This are provided using layer
    unpack_binary('/opt/headless-chrome/chromedriver.br', generator.CHROME_DRIVER_LOCATION)
    unpack_binary('/opt/headless-chrome/headless-chromium.br', generator.CHROME_BINARY_LOCATION)

    THUMBNAILERS = {
        ExtractorStatic.HTML: generator.WebThumbnailer,
        ExtractorStatic.PDF: generator.DocThumbnailer,
        ExtractorStatic.DOCX: generator.DocThumbnailer,
        ExtractorStatic.PPTX: generator.DocThumbnailer,
        ExtractorStatic.MSWORD: generator.DocThumbnailer,
    }

    thumbnailer = THUMBNAILERS.get(source.doc_type)
    if thumbnailer:
        if source.doc_type == ExtractorStatic.HTML:
            return thumbnailer(source.url, source.doc_type).get_thumbnail()
        else:
            return thumbnailer(source.get_file(), source.doc_type).get_thumbnail()
    else:
        raise Exception(f'Unexcepted doc_type: {source.doc_type}')


def source_thumbnail_extract_job_mapped_task_failure(event, *args, **kwargs):
    """
    Unexpected errors.
    """
    source_key = event['source_key']
    source = Source.get(source_key)
    source.thumbnail_status = Source.Status.FAILED
    source.save()
    return source.thumbnail_status


def source_thumbnail_generator(event, *args, **kwargs):
    source_key = event['source_key']
    source = get_or_none(Source, source_key)
    error_msg = None
    try:
        thumbnail = _get_thumbnail(source)
        if thumbnail:
            source.set_thumbnail(thumbnail)
            source.thumbnail_status = Source.Status.SUCCESS
        else:
            source.thumbnail_status = Source.Status.ERROR
    except Exception as e:
        error_msg = str(e)
        source.thumbnail_status = Source.Status.FAILED
        logger.error(f'Thumbnail failed for {source_key}', exc_info=True)
    source.save()

    if error_msg:
        return {
            'status': source.thumbnail_status,
            'error': error_msg,
        }
    return source.thumbnail_status
