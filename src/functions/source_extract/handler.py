import logging
import json
import os
import time
import boto3
from pdfminer.pdfdocument import PDFEncryptionError

from deep_serverless.utils import sentry  # noqa: F401

from deep_serverless.utils.decorators import LambdaDecorator, ValidationError
from deep_serverless.utils.validators import validator

from deep_serverless.models.source_extract import Source
from deep_serverless.models.base import AsyncJob

from .web_info_extract.sources import get_web_info_extractor
from .extractor.web_document import WebDocument
from .extractor.file_document import FileDocument

logger = logging.getLogger(__name__)

step_funtion = boto3.client('stepfunctions')


SOURCE_EXTRACT_EXPECTED_EXCEPTIONS = [PDFEncryptionError]


def source_extract_job_mapped_task(event, *args, **kwargs):
    source_key = event['source_key']
    error_msg = None

    source = Source.get(source_key)

    try:
        if source.type == Source.Type.WEB:
            doc = WebDocument(source.url)
        elif source.type == Source.Type.S3:
            doc = FileDocument(source.get_file(), source.s3_path)
        else:
            raise Exception(f'Invalid Source Type: {source.type}')

        (
            doc_type,
            text,
            images,
            page_count,
            word_count,
            file_size,
            extra_meta,
        ) = doc.extract()

        source.doc_type = doc_type
        source.last_extracted_at = time.time()
        source.set_simplified_text(text)
        source.extract.word_count = word_count
        source.extract.page_count = page_count
        source.extract.file_size = file_size
        source.extra_meta = extra_meta

        for image_name, image in images or []:
            source.upload_image(image_name, image)

        source.status = Source.Status.SUCCESS
    except Exception as e:
        (
            logger.error if type(e) not in SOURCE_EXTRACT_EXPECTED_EXCEPTIONS else logger.warning)(
                f'Failed to extract source: ({source.key}) {source.url or source.s3_path}', exc_info=True
        )
        error_msg = str(e)
        source.status = Source.Status.ERROR

    source.save()

    if error_msg:
        return {
            'status': source.status,
            'error': error_msg,
        }
    return source.status


def source_extract_job_mapped_task_failure(event, *args, **kwargs):
    """
    Unexpected errors.
    """
    source_key = event['source_key']
    source = Source.get(source_key)
    source.status = Source.Status.FAILED
    source.save()
    return source.status


def _source_extract_set_status(uuid, status):
    async_job = AsyncJob.get(uuid)
    async_job.status = status
    async_job.save()


def source_extract_job_success(event, *args, **kwargs):
    _source_extract_set_status(event['async_job_uuid'], AsyncJob.Status.SUCCESS)
    return event


def source_extract_job_failure(event, *args, **kwargs):
    _source_extract_set_status(event['async_job_uuid'], AsyncJob.Status.FAILED)
    return event


@LambdaDecorator
def main(event, *args, **kwargs):
    body = event.get('body') or {}
    requested_sources_from_client = body.get('sources') or []
    async_job_uuid = body.get('async_job_uuid')

    if async_job_uuid is not None:
        async_job = AsyncJob.get(async_job_uuid)
        if async_job.status == AsyncJob.Status.SUCCESS:
            return {
                'status': async_job.status,
                'sources': [
                    source.serialize()
                    for source in Source.batch_get(async_job.entities)
                ]
            }
        return {
            'status': async_job.status,
        }

    requested_sources = {}
    for meta in requested_sources_from_client:
        s3_path = None
        source_url = None
        invalidate = None

        if type(meta) == str:
            source_url = meta.get('url')
        elif type(meta) == dict:
            s3_path = meta.get('s3')
            source_url = meta.get('url')
            invalidate = meta.get('invalidate')
        else:
            raise ValidationError('Invalid body')

        if not any([s3_path, source_url]):
            raise ValidationError(f'Please specify s3 or url parameter for : {str(meta)}')

        if s3_path:
            requested_sources[Source.get_s3_key(s3_path)] = {
                's3_path': s3_path,
                'type': Source.Type.S3,
                'invalidate': invalidate,
            }
        else:
            requested_sources[Source.get_url_hash(source_url)] = {
                'url': source_url,
                'type': Source.Type.WEB,
                'invalidate': invalidate,
            }

    existing_sources = []
    to_be_processed_sources = []
    with Source.batch_write() as source_batch:
        # Existing sources
        for source in Source.batch_get(requested_sources.keys()):
            invalidate = requested_sources[source.key]['invalidate']
            # if not invalidate and source.status in [Source.Status.FAILED, Source.Status.ERROR, Source.Status.SUCCESS]:
            if not invalidate and source.status in [Source.Status.ERROR, Source.Status.SUCCESS]:
                existing_sources.append(source.serialize())
            else:
                to_be_processed_sources.append({'source_key': source.key})
            requested_sources.pop(source.key)

        # New sources
        for source_key, meta in requested_sources.items():
            meta.pop('invalidate')
            source = Source(
                key=source_key,
                **meta,
            )
            source_batch.save(source)
            to_be_processed_sources.append({'source_key': source.key})

    async_job = None
    if to_be_processed_sources:
        async_job = AsyncJob()
        async_job.type = AsyncJob.Type.SOURCE_EXTRACT
        async_job.entities = [source['source_key'] for source in to_be_processed_sources]
        async_job.save()
        # TODO: Offline doesn't work
        step_funtion.start_execution(
            stateMachineArn=os.environ['SOURCE_EXTRACT_STATE_MACHINE_ARN'],
            name=f"async-job-{async_job.uuid}",
            input=json.dumps({
                'async_job_uuid': async_job.uuid,
                'sources': to_be_processed_sources,
            }),
        )

    return {
        'existing_sources': existing_sources,
        'async_job_uuid': async_job and async_job.uuid,
    }


# TODO: REMOVE THIS (LEGACY)
@LambdaDecorator
def web_info_extract(event, *args, **kwargs):
    params = event.get('queryStringParameters') or {}
    url = params.get('url') or ''

    # TODO: Use schema validator
    if not url or not validator.is_url(url):
        raise ValidationError({'url': f'Url <{url}> must be present and valid'})

    doc_type, doc = WebDocument.get_document(url)
    extractor = get_web_info_extractor(url, content=doc, document_type=doc_type)
    return extractor.get_serialized_data()
