import os

from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.utils.encoding import filepath_to_uri

try:
    from storages.backends.s3 import S3Storage
except ImportError:
    from storages.backends.s3boto3 import S3Boto3Storage as S3Storage


class BaseContentFilesStorage(S3Storage):
    def __init__(self, *args, **kwargs):
        # contentfiles specific settings
        self.contentfiles_prefix = settings.CONTENTFILES_PREFIX
        self.contentfiles_ssl = getattr(settings, "CONTENTFILES_SSL", True)
        self.contentfiles_hostname = getattr(settings, "CONTENTFILES_HOSTNAME", None)
        self.contentfiles_s3_endpoint_url = getattr(settings, "CONTENTFILES_S3_ENDPOINT_URL", None)
        self.contentfiles_s3_region = getattr(settings, "CONTENTFILES_S3_REGION", None)

        # django-storages settings
        self.location = f"{self.contentfiles_prefix}/"
        self.access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.file_overwrite = False
        self.default_acl = None  # Use the default ACL from the bucket
        self.addressing_style = "virtual"

        # Send requests direct to the region when defined
        self.endpoint_url = self.contentfiles_s3_endpoint_url
        # Define the region to allow signed URLs to fully work
        self.region_name = self.contentfiles_s3_region

        super().__init__(*args, **kwargs)


class MediaStorage(BaseContentFilesStorage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = os.environ.get("CONTENTFILES_DEFAULT_BUCKET")

        super().__init__(*args, **kwargs)

    def url(self, name):
        protocol = "https" if self.contentfiles_ssl else "http"

        if self.contentfiles_hostname is None:
            hostname = f"{self.contentfiles_prefix}.contentfiles.net"
        else:
            hostname = self.contentfiles_hostname

        return f"{protocol}://{hostname}/media/{filepath_to_uri(name)}"


class PrivateStorage(BaseContentFilesStorage):
    def __init__(self, *args, **kwargs):
        # Reduced expiry time to prevent URL sharing (but high enough to not expire too quickly)
        self.bucket_name = os.environ.get("CONTENTFILES_PRIVATE_BUCKET")
        self.querystring_expire = 300

        super().__init__(*args, **kwargs)


def private_storage():
    if os.environ.get("CONTENTFILES_PRIVATE_BUCKET") is not None:
        return PrivateStorage()
    return DefaultStorage()
