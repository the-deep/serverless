import time
import hashlib
import uuid
import os
import json

from pynamodb.models import Model
from pynamodb.attributes import (
    MapAttribute,
    UnicodeAttribute,
    NumberAttribute,
    UnicodeSetAttribute,
    JSONAttribute as PydbJSONAttribute,
)

from src.common.django_utils import DjangoJSONEncoder


class JSONAttribute(PydbJSONAttribute):

    def serialize(self, value):
        """
        Serializes JSON to unicode
        """
        if value is None:
            return None
        encoded = json.dumps(value, cls=DjangoJSONEncoder)
        return encoded


class Status():
    PENDING: str = 'pending'
    STARTED: str = 'started'
    SUCCESS: str = 'success'
    ERROR: str = 'error'


class SourceType():
    WEB: str = 'web'


class LeadExtract(MapAttribute):
    simplified_text = UnicodeAttribute(default='')
    word_count = NumberAttribute(null=True)
    page_count = NumberAttribute(null=True)
    file_size = NumberAttribute(null=True)


class BaseModelMeta():
    if os.getenv('IS_OFFLINE', False):
        host: str = 'http://localhost:8000'
        aws_access_key_id: str = 'DEFAULT_ACCESS_KEY'
        aws_secret_access_key: str = 'DEFAULT_SECRET'


class Source(Model):
    class Meta(BaseModelMeta):
        table_name: str = os.getenv('SOURCE_TABLE_NAME')

    @staticmethod
    def get_url_hash(url):
        return hashlib.sha224(url.encode()).hexdigest()

    # Make sure to update serverlesss.yml
    hash = UnicodeAttribute(hash_key=True)
    url = UnicodeAttribute(null=False)
    status = UnicodeAttribute(default=Status.PENDING)
    last_extracted_at = NumberAttribute(null=True)  # Epoch
    type = UnicodeAttribute()
    extract = LeadExtract(default=dict)
    # Store extra information
    extra_meta = JSONAttribute(null=True)

    def serialize(self):
        # TODO: Use serializer utils
        return {
            'hash': self.hash,
            'url': self.url,
            'status': self.status,
            'last_extracted_at': self.last_extracted_at,
            'type': self.type,
            'extra_meta': self.extra_meta,
            # 'extract': {
            #     'simplified_text': self.extract.simplified_text,
            #     'word_count': self.extract.word_count,
            #     'page_count': self.extract.page_count,
            #     'file_size': self.extract.file_size,
            # },
        }


class AsyncJobType():
    SOURCE_EXTRACT: str = 'source_extract'


class AsyncJob(Model):
    class Meta(BaseModelMeta):
        table_name: str = os.getenv('ASYNC_JOB_TABLE_NAME')

    uuid = UnicodeAttribute(hash_key=True, default=lambda: str(uuid.uuid4()))
    status = UnicodeAttribute(default=Status.PENDING)
    type = UnicodeAttribute()
    # Store hash key of the entities here
    entities = UnicodeSetAttribute()
    ttl = NumberAttribute(default=lambda: int(time.time()) + 86400)  # 1 day
