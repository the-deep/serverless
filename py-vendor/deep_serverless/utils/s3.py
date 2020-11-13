# SOURCE: https://github.com/django/django/blob/master/django/core/files/storage.py
# SOURCE: https://github.com/jschneier/django-storages/blob/master/storages/backends/s3boto3.py
# NOTE: Only copied used part.

import io
import os
import boto3
import posixpath
import mimetypes
from gzip import GzipFile
from tempfile import SpooledTemporaryFile
from botocore.exceptions import ClientError

from .common import get_random_string


def force_bytes(s):
    if isinstance(s, bytes):
        return s
    if isinstance(s, memoryview):
        return bytes(s)
    return str(s).encode('utf-8', 'strict')


def safe_join(base, *paths):
    base_path = base
    base_path = base_path.rstrip('/')
    paths = [p for p in paths]
    final_path = base_path + '/'
    for path in paths:
        _final_path = posixpath.normpath(posixpath.join(final_path, path))
        # posixpath.normpath() strips the trailing /. Add it back.
        if path.endswith('/') or _final_path + '/' == final_path:
            _final_path += '/'
        final_path = _final_path
    if final_path == base_path:
        final_path += '/'
    base_path_len = len(base_path)
    if (not final_path.startswith(base_path) or final_path[base_path_len] != '/'):
        raise ValueError('the joined path is located outside of the base path component')
    return final_path.lstrip('/')


class Storage():
    DEFAULT_CONTENT_TYPE = 'application/octet-stream'
    DEFAULT_QUERYSTRING_EXPIRE = 3600  # 1 hour

    QUERYSTRING_AUTH = True
    GZIP_CONTENT_TYPES = [
        'text/javascript', 'application/javascript', 'application/x-javascript',
        'image/svg+xml', 'application/json', 'text/css',
    ]

    def __init__(self, bucket_name, base_path):
        self.bucket_name = bucket_name
        self.base_path = base_path
        self._file = None

    @property
    def connection(self):
        connection = getattr(self, '_connection', None)
        if connection is None:
            session = boto3.session.Session()
            self._connection = session.resource('s3')
        return self._connection

    @property
    def bucket(self):
        bucket = getattr(self, '_bucket', None)
        if bucket is None:
            self._bucket = self.connection.Bucket(self.bucket_name)
        return self._bucket

    def exists(self, name):
        name = self._normalize_name(name)
        try:
            self.connection.meta.client.head_object(Bucket=self.bucket_name, Key=name)
            return True
        except ClientError:
            return False

    def get_alternative_name(self, file_root, file_ext):
        return '%s_%s%s' % (file_root, get_random_string(7), file_ext)

    # NOTE: max_length is defined by the max_length for django FileField default configuration. (Don't change this here)
    def get_available_name(self, name, max_length=100):
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        while self.exists(name) or (max_length and len(name) > max_length):
            name = os.path.join(dir_name, self.get_alternative_name(file_root, file_ext))
            if max_length is None:
                continue
            truncation = len(name) - max_length
            if truncation > 0:
                file_root = file_root[:-truncation]
                if not file_root:
                    raise Exception(f"Can't generate filename for '{name}' due to s3 key size limit.")
                name = os.path.join(dir_name, self.get_alternative_name(file_root, file_ext))
        return name

    def _compress_content(self, content):
        """Gzip a given string content."""
        content.seek(0)
        zbuf = io.BytesIO()
        zfile = GzipFile(mode='wb', fileobj=zbuf, mtime=0.0)
        try:
            zfile.write(force_bytes(content.read()))
        finally:
            zfile.close()
        zbuf.seek(0)
        return zbuf

    def _clean_name(self, name):
        clean_name = posixpath.normpath(name).replace('\\', '/')
        if name.endswith('/') and not clean_name.endswith('/'):
            clean_name += '/'
        return clean_name

    def _normalize_name(self, name):
        try:
            return safe_join(self.base_path, name)
        except ValueError:
            raise Exception("Attempted access to '%s' denied." % name)

    def _get_write_parameters(self, name, content=None):
        params = {}
        _type, encoding = mimetypes.guess_type(name)
        content_type = getattr(content, 'content_type', None)
        content_type = content_type or _type or self.DEFAULT_CONTENT_TYPE
        params['ContentType'] = content_type
        if encoding:
            params['ContentEncoding'] = encoding
        return params

    def upload(self, name, content, gzip=True):
        if not name:
            raise Exception('Name is required')
        cleaned_name = self.get_available_name(self._clean_name(name))
        name = self._normalize_name(cleaned_name)
        params = self._get_write_parameters(name, content)
        if (
            gzip and
            params['ContentType'] in self.GZIP_CONTENT_TYPES and
            'ContentEncoding' not in params
        ):
            content = self._compress_content(content)
            params['ContentEncoding'] = 'gzip'
        content.seek(0, os.SEEK_SET)
        obj = self.bucket.Object(name)
        obj.upload_fileobj(content, ExtraArgs=params)
        return cleaned_name

    def url(self, name, parameters=None, expire=None, http_method=None):
        name = self._normalize_name(self._clean_name(name))
        if expire is None:
            expire = self.DEFAULT_QUERYSTRING_EXPIRE
        params = parameters.copy() if parameters else {}
        params['Bucket'] = self.bucket.name
        params['Key'] = name
        url = self.bucket.meta.client.generate_presigned_url(
            'get_object', Params=params, ExpiresIn=expire, HttpMethod=http_method
        )
        if self.QUERYSTRING_AUTH:
            return url
        return self._strip_signing_parameters(url)

    def get_file(self, name):
        name = self._normalize_name(self._clean_name(name))
        file = SpooledTemporaryFile(
            suffix=".S3Boto3StorageFile",
            dir='/tmp/'
        )
        obj = self.bucket.Object(name)
        obj.download_fileobj(file)
        file.seek(0)
        return file
