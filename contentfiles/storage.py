import os

from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.utils.encoding import filepath_to_uri

from storages.backends.s3boto3 import S3Boto3Storage

CONTENTFILES_SSL = getattr(settings, "CONTENTFILES_SSL", True)
CONTENTFILES_PREFIX = getattr(settings, "CONTENTFILES_PREFIX")
CONTENTFILES_HOSTNAME = getattr(settings, "CONTENTFILES_HOSTNAME", None)
CONTENTFILES_S3_ENDPOINT_URL = getattr(settings, "CONTENTFILES_S3_ENDPOINT_URL", None)
CONTENTFILES_S3_REGION = getattr(settings, "CONTENTFILES_S3_REGION", None)


class BaseContentFilesStorage(S3Boto3Storage):
    location = "{}/".format(CONTENTFILES_PREFIX)
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    file_overwrite = False
    default_acl = None  # Use the default ACL from the bucket
    addressing_style = "virtual"
    endpoint_url = CONTENTFILES_S3_ENDPOINT_URL  # Send requests direct to the region when defined
    region_name = CONTENTFILES_S3_REGION  # Define the region to allow signed URLs to fully work


class MediaStorage(BaseContentFilesStorage):
    bucket_name = os.environ.get("CONTENTFILES_DEFAULT_BUCKET")

    def url(self, name):
        protocol = "https" if CONTENTFILES_SSL else "http"

        if CONTENTFILES_HOSTNAME is None:
            hostname = "{}.contentfiles.net".format(CONTENTFILES_PREFIX)
        else:
            hostname = CONTENTFILES_HOSTNAME

        return "{}://{}/media/{}".format(protocol, hostname, filepath_to_uri(name))


class RemotePrivateStorage(BaseContentFilesStorage):
    bucket_name = os.environ.get("CONTENTFILES_PRIVATE_BUCKET")
    querystring_expire = 300


if os.environ.get("CONTENTFILES_PRIVATE_BUCKET") is not None:
    BasePrivateStorage = RemotePrivateStorage
else:
    BasePrivateStorage = DefaultStorage


class PrivateStorage(BasePrivateStorage):
    pass


private_storage = PrivateStorage()
