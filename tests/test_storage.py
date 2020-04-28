import datetime
from unittest import mock
from urllib import parse

from django.test import TestCase, override_settings

from contentfiles.storage import MediaStorage, RemotePrivateStorage


class TestMediaStorage(TestCase):
    def test_url(self):
        storage = MediaStorage()

        url = storage.url("test.txt")

        self.assertEqual(url, "https://demo.contentfiles.net/media/test.txt")

    def test_unicode_url(self):
        storage = MediaStorage()

        url = storage.url("Paris+&+Orléans.jpg")

        self.assertEqual(url, "https://demo.contentfiles.net/media/Paris%2B%26%2BOrl%C3%A9ans.jpg")

    @override_settings(CONTENTFILES_SSL=False)
    def test_http_url(self):
        storage = MediaStorage()

        url = storage.url("test.txt")

        self.assertEqual(url, "http://demo.contentfiles.net/media/test.txt")

    @override_settings(CONTENTFILES_HOSTNAME="media.example.org")
    def test_custom_hostname(self):
        storage = MediaStorage()

        url = storage.url("test.txt")

        self.assertEqual(url, "https://media.example.org/media/test.txt")

    @mock.patch("botocore.auth.HmacV1QueryAuth._get_date")
    def test_private_storage(self, mock_get_date):
        mock_get_date.return_value = "1234567890"

        storage = RemotePrivateStorage()
        storage.access_key = "AKIA1234567890ABCDEF"
        storage.secret_key = "1234567890123456789012345678901234567890"
        storage.bucket_name = "demo-bucket"

        url = storage.url("test.txt")

        parsed_url = parse.urlparse(url)
        url_querystring = parse.parse_qs(parsed_url.query)

        self.assertEqual(parsed_url.scheme, "https")
        self.assertEqual(parsed_url.netloc, "demo-bucket.s3.amazonaws.com")
        self.assertEqual(parsed_url.path, "/demo/test.txt")
        self.assertDictEqual(
            url_querystring,
            {
                "AWSAccessKeyId": ["AKIA1234567890ABCDEF"],
                "Signature": ["nolnfqXilquat3YAccmhEyNk/IU="],
                "Expires": ["1234567890"],
            },
        )

    @override_settings(
        CONTENTFILES_S3_REGION="eu-west-2",
        CONTENTFILES_S3_ENDPOINT_URL="https://s3.dualstack.eu-west-2.amazonaws.com",
    )
    @mock.patch("botocore.auth.datetime")
    def test_private_storage_aws4(self, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 1, 1, 12, 34, 56, 0)

        storage = RemotePrivateStorage()
        storage.access_key = "AKIA1234567890ABCDEF"
        storage.secret_key = "1234567890123456789012345678901234567890"
        storage.bucket_name = "demo-bucket"

        url = storage.url("test.txt")

        parsed_url = parse.urlparse(url)
        url_querystring = parse.parse_qs(parsed_url.query)

        self.assertEqual(parsed_url.scheme, "https")
        self.assertEqual(parsed_url.netloc, "demo-bucket.s3.dualstack.eu-west-2.amazonaws.com")
        self.assertEqual(parsed_url.path, "/demo/test.txt")
        self.assertDictEqual(
            url_querystring,
            {
                "X-Amz-Algorithm": ["AWS4-HMAC-SHA256"],
                "X-Amz-Credential": ["AKIA1234567890ABCDEF/20200101/eu-west-2/s3/aws4_request"],
                "X-Amz-Date": ["20200101T123456Z"],
                "X-Amz-Expires": ["300"],
                "X-Amz-Signature": [
                    "be39d90daf58c495bde25a607e20dbf2f75f4d01358a5bc93911a2733bd3da21"
                ],
                "X-Amz-SignedHeaders": ["host"],
            },
        )
