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
from src.common.s3 import Storage


deep_media_storage = Storage(
    os.environ['MEDIA_BUCKET_NAME'],
    os.environ['MEDIA_BUCKET_ROOT'],
)


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
    ERROR: str = 'error'  # expected
    FAILED: str = 'failed'  # unexpected


class SourceType():
    WEB: str = 'web'
    S3: str = 's3'


class LeadExtract(MapAttribute):
    simplified_text = UnicodeAttribute(default='')
    word_count = NumberAttribute(null=True)
    page_count = NumberAttribute(null=True)
    file_size = NumberAttribute(null=True)


class BaseModelMeta():
    if os.environ.get('IS_OFFLINE', False):
        host: str = 'http://localhost:8000'
        aws_access_key_id: str = 'DEFAULT_ACCESS_KEY'
        aws_secret_access_key: str = 'DEFAULT_SECRET'


class Source(Model):
    # Make sure to update serverlesss.yml
    key = UnicodeAttribute(hash_key=True)  # Hash for url and `s3:<path>` for s3 objects
    # Make sure one of (url, s3_path) is defined
    url = UnicodeAttribute(null=True)
    s3_path = UnicodeAttribute(null=True)
    status = UnicodeAttribute(default=Status.PENDING)
    last_extracted_at = NumberAttribute(null=True)  # Epoch
    type = UnicodeAttribute()
    doc_type = UnicodeAttribute(null=True)
    extract = LeadExtract(default=dict)
    images = UnicodeSetAttribute(default=set())
    # Store extra information
    extra_meta = JSONAttribute(null=True)

    class Meta(BaseModelMeta):
        table_name: str = os.environ['SOURCE_TABLE_NAME']

    @staticmethod
    def get_url_hash(url):
        return hashlib.sha224(url.encode()).hexdigest()

    @staticmethod
    def get_s3_key(s3_path):
        return f's3::{s3_path}'

    @property
    def usable_url(self):
        # Return url which can be used to access resource (web page, s3 file)
        if self.type == SourceType.WEB:
            return self.url
        if self.type == SourceType.S3:
            return deep_media_storage.url(self.s3_path)

    def get_file(self):
        if self.s3_path and self.type == SourceType.S3:
            return deep_media_storage.get_file(self.s3_path)
        return None

    def upload_image(self, name, image):
        image_s3_path = deep_media_storage.upload(
            os.path.join('lead-preview/from-lambda/', name),
            image,
        )
        self.images.add(image_s3_path)

    def serialize(self):
        # TODO: Use serializer utils
        return {
            'key': self.key,
            'url': self.url,
            'type': self.type,
            'status': self.status,
            'last_extracted_at': self.last_extracted_at,
            'extra_meta': self.extra_meta,
        }


class AsyncJobType():
    SOURCE_EXTRACT: str = 'source_extract'


class AsyncJob(Model):
    class Meta(BaseModelMeta):
        table_name: str = os.environ['ASYNC_JOB_TABLE_NAME']

    uuid = UnicodeAttribute(hash_key=True, default=lambda: str(uuid.uuid4()))
    status = UnicodeAttribute(default=Status.PENDING)
    type = UnicodeAttribute()
    # Store key of the entities here
    entities = UnicodeSetAttribute()
    ttl = NumberAttribute(default=lambda: int(time.time()) + 86400)  # 1 day
