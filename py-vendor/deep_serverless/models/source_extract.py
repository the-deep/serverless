import hashlib
import os
import sys

from pynamodb.models import Model
from pynamodb.attributes import (
    MapAttribute,
    UnicodeAttribute,
    NumberAttribute,
    UnicodeSetAttribute,
)

from ..utils.common import setting
from ..utils.django_utils.file import ContentFile

from .base import (
    deep_media_storage,

    BaseModelMeta,
    JSONAttribute,
)


class LeadExtract(MapAttribute):
    simplified_text = UnicodeAttribute(null=True)
    simplified_text_s3_key = UnicodeAttribute(null=True)
    word_count = NumberAttribute(null=True)
    page_count = NumberAttribute(null=True)
    file_size = NumberAttribute(null=True)


class Source(Model):
    class Status():
        PENDING: str = 'pending'
        STARTED: str = 'started'
        SUCCESS: str = 'success'
        ERROR: str = 'error'  # expected
        FAILED: str = 'failed'  # unexpected
        NOT_PROCESSED: str = 'not_processed'

    class Type():
        WEB: str = 'web'
        S3: str = 's3'

    # Make sure to update serverlesss.yml
    key = UnicodeAttribute(hash_key=True)  # Hash for url and `s3:<path>` for s3 objects
    # Make sure one of (url, s3_path) is defined
    url = UnicodeAttribute(null=True)
    s3_path = UnicodeAttribute(null=True)
    last_extracted_at = NumberAttribute(null=True)  # Epoch
    type = UnicodeAttribute()
    doc_type = UnicodeAttribute(null=True)
    extract = LeadExtract(default=dict)
    images = UnicodeSetAttribute(default=set())
    # Store extra information
    extra_meta = JSONAttribute(null=True)
    status = UnicodeAttribute(default=Status.PENDING)
    extract_status = UnicodeAttribute(default=Status.NOT_PROCESSED)
    thumbnail_status = UnicodeAttribute(default=Status.NOT_PROCESSED)

    class Meta(BaseModelMeta):
        table_name: str = setting('SOURCE_TABLE_NAME')

    @staticmethod
    def get_url_hash(url):
        return hashlib.sha224(url.encode()).hexdigest()

    @staticmethod
    def get_s3_key(s3_path):
        return f's3::{s3_path}'

    @property
    def usable_url(self):
        # Return url which can be used to access resource (web page, s3 file)
        if self.type == Source.Type.WEB:
            return self.url
        if self.type == Source.Type.S3:
            return deep_media_storage.url(self.s3_path)

    def get_file(self):
        if self.s3_path and self.type == Source.Type.S3:
            return deep_media_storage.get_file(self.s3_path)
        return None

    def upload_image(self, name, image):
        image_s3_path = deep_media_storage.upload(
            # This is from the-deep/server apps/lead/models.py:LeadPreviewImage:file
            os.path.join('lead-preview/from-lambda/', name),
            image,
        )
        self.images.add(image_s3_path)

    def set_simplified_text(self, text):
        if self.key is None:
            raise Exception('key needs to be defined')

        # Safe value (dynamodb item should not exceed 400K), TODO: Check for absolute
        if sys.getsizeof(text) < 400000:
            self.extract.simplified_text = text
        else:
            simplified_text_s3_key = deep_media_storage.upload(
                f'serverless/source-simplified-text/{self.key}.txt',
                ContentFile(text.encode('utf-8')),
            )
            self.extract.simplified_text_s3_key = simplified_text_s3_key

    def get_simplified_text(self):
        # NOTE: This may require KMS key access if files are encrypted in S3
        s3_key = self.extract.simplified_text_s3_key
        if s3_key:
            return deep_media_storage.get_file(s3_key).read().decode('utf-8')
        return self.extract.simplified_text

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
