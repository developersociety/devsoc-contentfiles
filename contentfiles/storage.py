from __future__ import unicode_literals

import os

from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.utils.six.moves import urllib

from boto.s3.connection import S3Connection
from storages.backends.s3boto import S3BotoStorage


CONTENTFILES_SSL = getattr(settings, 'CONTENTFILES_SSL', True)
CONTENTFILES_PREFIX = getattr(settings, 'CONTENTFILES_PREFIX')
CONTENTFILES_HOSTNAME = getattr(settings, 'CONTENTFILES_HOSTNAME', None)
CONTENTFILES_S3_ENDPOINT = getattr(settings, 'CONTENTFILES_S3_ENDPOINT', S3Connection.DefaultHost)


class BaseContentFilesStorage(S3BotoStorage):
    location = '%s/' % (CONTENTFILES_PREFIX,)
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    file_overwrite = False
    default_acl = None  # Use the default ACL from the bucket
    host = CONTENTFILES_S3_ENDPOINT  # Send requests direct to the region when defined


class MediaStorage(BaseContentFilesStorage):
    bucket_name = os.environ.get('CONTENTFILES_DEFAULT_BUCKET')

    def url(self, name):
        protocol = 'https' if CONTENTFILES_SSL else 'http'

        if CONTENTFILES_HOSTNAME is None:
            hostname = '%s.contentfiles.net' % (CONTENTFILES_PREFIX,)
        else:
            hostname = CONTENTFILES_HOSTNAME

        return '%s://%s/media/%s' % (
            protocol, hostname, urllib.parse.quote(name.encode('utf-8')))


class RemotePrivateStorage(BaseContentFilesStorage):
    bucket_name = os.environ.get('CONTENTFILES_PRIVATE_BUCKET')
    querystring_expire = 300


if os.environ.get('CONTENTFILES_PRIVATE_BUCKET') is not None:
    BasePrivateStorage = RemotePrivateStorage
else:
    BasePrivateStorage = DefaultStorage


class PrivateStorage(BasePrivateStorage):
    pass


private_storage = PrivateStorage()
