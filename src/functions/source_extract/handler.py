import logging
import json
import boto3
import os
import time

from src.common.decorators import LambdaDecorator, ValidationError
from src.common.validators import validator

from .web_info_extract.sources import get_web_info_extractor
from .extractor.web_document import WebDocument
from .models import (
    Status,
    AsyncJob,
    AsyncJobType,
    Source,
    SourceType,
)

logger = logging.getLogger(__name__)

StepFuntion = boto3.client('stepfunctions')


def source_extract_job_mapped_task(event, *args, **kwargs):
    url = event['url']
    source_hash = event['hash']
    error_msg = None

    source = Source.get(source_hash)
    try:
        doc = WebDocument(url)
        text, images, page_count, extra_meta = doc.extract()
        source.last_extracted_at = time.time()
        source.extract.simplified_text = text
        source.extract.word_count = len(text.split(' '))
        source.extract.page_count = page_count
        source.extra_meta = extra_meta
        source.status = Status.SUCCESS
    except Exception as e:
        logging.error(f'Failed to extract url: {url}', exc_info=True)
        error_msg = str(e)
        source.status = Status.ERROR
    source.save()

    if error_msg:
        return {
            'status': source.status,
            'error': error_msg,
        }
    return source.status


def source_extract_job_success(event, *args, **kwargs):
    async_job = AsyncJob.get(event['async_job_uuid'])
    async_job.status = Status.SUCCESS
    async_job.save()


@LambdaDecorator
def main(event, *args, **kwargs):
    body = event.get('body') or {}
    sources_url = body.get('sources')
    async_job_uuid = body.get('async_job_uuid')

    if async_job_uuid is not None:
        async_job = AsyncJob.get(async_job_uuid)
        if async_job.status == Status.SUCCESS:
            return {
                'sources': [
                    source.serialize()
                    for source in Source.batch_get(async_job.entities)
                ]
            }
        return {
            'status': async_job.status,
        }

    requested_sources = {
        Source.get_url_hash(url): url
        for url in sources_url
    }

    existing_sources = []
    to_be_processed_sources = []
    with Source.batch_write() as source_batch:
        for source in Source.batch_get(requested_sources.keys()):
            if source.status in [Status.ERROR, Status.SUCCESS]:
                existing_sources.append(source.serialize())
            else:
                to_be_processed_sources.append(source)
            requested_sources.pop(source.hash)

        for url_hash, url in requested_sources.items():
            source = Source(
                hash=url_hash,
                url=url,
                type=SourceType.WEB,
            )
            source_batch.save(source)
            to_be_processed_sources.append(source)

    async_job = None
    if to_be_processed_sources:
        async_job = AsyncJob()
        async_job.type = AsyncJobType.SOURCE_EXTRACT
        async_job.entities = [source.hash for source in to_be_processed_sources]
        async_job.save()
        # TODO: Offline doesn't work
        StepFuntion.start_execution(
            stateMachineArn=os.getenv('SOURCE_EXTRACT_STATE_MACHINE_ARN'),
            name=f"async-job-{async_job.uuid}",
            input=json.dumps({
                'async_job_uuid': async_job.uuid,
                'sources': [
                    {
                        'hash': source.hash,
                        'url': source.url,
                    }
                    for source in to_be_processed_sources
                ],
            }),
        )

    return {
        'existing_sources': existing_sources,
        'async_job_uuid': async_job and async_job.uuid,
    }


# TODO: REMOVE THIS (LEGACY)
@LambdaDecorator
def web_info_extract(event, *args, **kwargs):
    params = event.get('query_string_parameters') or {}
    url = params.get('url') or ''

    # TODO: Use schema validator
    if not url or not validator.is_url(url):
        raise ValidationError({'url': f'Url <{url}> must be present and valid'})

    doc_type = WebDocument.get_document_type(url)
    extractor = get_web_info_extractor(url, document_type=doc_type)
    return extractor.get_serialized_data()
