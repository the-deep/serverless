import time
import uuid
import json

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UnicodeSetAttribute,
    JSONAttribute as PydbJSONAttribute,
)

from ..utils.common import setting
from ..utils.django_utils.common import DjangoJSONEncoder
from ..utils.s3 import Storage


deep_media_storage = Storage(
    setting('MEDIA_BUCKET_NAME'),
    setting('MEDIA_BUCKET_ROOT', 'media'),
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


class BaseModelMeta():
    if setting('IS_OFFLINE', False):
        host: str = 'http://localhost:8000'
        aws_access_key_id: str = 'DEFAULT_ACCESS_KEY'
        aws_secret_access_key: str = 'DEFAULT_SECRET'


class AsyncJob(Model):
    class Status():
        PENDING: str = 'pending'
        STARTED: str = 'started'
        SUCCESS: str = 'success'
        ERROR: str = 'error'  # expected
        FAILED: str = 'failed'  # unexpected

    class Type():
        SOURCE_EXTRACT: str = 'source_extract'

    class Meta(BaseModelMeta):
        table_name: str = setting('ASYNC_JOB_TABLE_NAME')

    uuid = UnicodeAttribute(hash_key=True, default=lambda: str(uuid.uuid4()))
    status = UnicodeAttribute(default=Status.PENDING)
    type = UnicodeAttribute()
    # Store key of the entities here
    entities = UnicodeSetAttribute()
    ttl = NumberAttribute(default=lambda: int(time.time()) + 86400)  # 1 day
