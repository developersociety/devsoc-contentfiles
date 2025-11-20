import io
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.test import TestCase

from contentfiles.fallback_sync_storage import LocalFallbackSyncStorage


class LocalFallbackSyncStorageTestCase(TestCase):
    """Test the LocalFallbackSyncStorage backend."""

    def setUp(self):
        """Set up mock fallback storage for tests."""
        # Create a mock fallback storage
        self.mock_fallback = Mock()
        self.storage = LocalFallbackSyncStorage(fallback="contentfiles.storage.MediaStorage")

        # Replace the fallback with our mock
        self.storage._fallback_storage = self.mock_fallback

    def test_initialization_without_fallback(self):
        """Test that storage can be initialized without a fallback (with warning)."""
        with self.assertLogs("contentfiles.fallback_sync_storage", level="WARNING"):
            storage = LocalFallbackSyncStorage()
            self.assertIsNone(storage._fallback_storage)

    def test_initialization_with_invalid_fallback(self):
        """Test that invalid fallback path raises ImproperlyConfigured."""
        with self.assertRaises(ImproperlyConfigured):
            LocalFallbackSyncStorage(fallback="invalid.module.path.Storage")

    def test_exists_local_file(self):
        """Test exists() returns True for files that exist locally."""
        # Mock the parent exists to return True (file exists locally)
        with patch("django.core.files.storage.FileSystemStorage.exists", return_value=True):
            result = self.storage.exists("test.txt")

            self.assertTrue(result)
            # Fallback should not be checked
            self.mock_fallback.exists.assert_not_called()

    def test_exists_syncs_from_fallback(self):
        """Test exists() syncs file from fallback if not local."""
        # File doesn't exist locally
        # But exists in fallback
        self.mock_fallback.exists.return_value = True
        self.mock_fallback.open.return_value.__enter__ = Mock(
            return_value=io.BytesIO(b"test content")
        )
        self.mock_fallback.open.return_value.__exit__ = Mock(return_value=False)

        with (
            patch("django.core.files.storage.FileSystemStorage.exists", return_value=False),
            patch("django.core.files.storage.FileSystemStorage.save") as mock_save,
        ):
            result = self.storage.exists("test.txt")

            self.assertTrue(result)
            self.mock_fallback.exists.assert_called_once_with("test.txt")
            mock_save.assert_called_once()

    def test_exists_returns_false_when_nowhere(self):
        """Test exists() returns False when file is in neither storage."""
        with patch("django.core.files.storage.FileSystemStorage.exists", return_value=False):
            self.mock_fallback.exists.return_value = False

            result = self.storage.exists("nonexistent.txt")

            self.assertFalse(result)

    def test_open_read_mode_syncs_from_fallback(self):
        """Test open() in read mode syncs from fallback if not local."""
        self.mock_fallback.exists.return_value = True
        mock_file = io.BytesIO(b"test content")
        self.mock_fallback.open.return_value.__enter__ = Mock(return_value=mock_file)
        self.mock_fallback.open.return_value.__exit__ = Mock(return_value=False)

        with (
            patch("django.core.files.storage.FileSystemStorage.exists", return_value=False),
            patch("django.core.files.storage.FileSystemStorage.save"),
            patch("django.core.files.storage.FileSystemStorage.open"),
        ):
            self.storage.open("test.txt", "rb")

            # Should have tried to sync
            self.mock_fallback.exists.assert_called_once()

    def test_open_write_mode_no_fallback_check(self):
        """Test open() in write mode doesn't check fallback."""
        with patch("django.core.files.storage.FileSystemStorage.open") as mock_open:
            self.storage.open("test.txt", "wb")

            # Should not have checked fallback
            self.mock_fallback.exists.assert_not_called()
            mock_open.assert_called_once_with("test.txt", "wb")

    def test_save_only_local(self):
        """Test save() only writes to local storage, not fallback."""
        content = ContentFile(b"test content")

        with patch("django.core.files.storage.FileSystemStorage.save") as mock_save:
            mock_save.return_value = "test.txt"

            result = self.storage.save("test.txt", content)

            self.assertEqual(result, "test.txt")
            mock_save.assert_called_once()
            # Fallback should never be touched
            self.assertFalse(
                hasattr(self.mock_fallback, "save") and self.mock_fallback.save.called
            )

    def test_delete_only_local(self):
        """Test delete() only deletes from local storage, not fallback."""
        with patch("django.core.files.storage.FileSystemStorage.delete") as mock_delete:
            self.storage.delete("test.txt")

            mock_delete.assert_called_once_with("test.txt")
            # Fallback should never be touched
            self.assertFalse(
                hasattr(self.mock_fallback, "delete") and self.mock_fallback.delete.called
            )

    def test_size_syncs_from_fallback(self):
        """Test size() syncs file from fallback if not local."""
        self.mock_fallback.exists.return_value = True
        mock_file = io.BytesIO(b"test content")
        self.mock_fallback.open.return_value.__enter__ = Mock(return_value=mock_file)
        self.mock_fallback.open.return_value.__exit__ = Mock(return_value=False)

        with (
            patch("django.core.files.storage.FileSystemStorage.exists", return_value=False),
            patch("django.core.files.storage.FileSystemStorage.save"),
            patch("django.core.files.storage.FileSystemStorage.size", return_value=100),
        ):
            result = self.storage.size("test.txt")

            self.assertEqual(result, 100)
            # Should have synced from fallback
            self.mock_fallback.exists.assert_called_once()

    def test_url_returns_local_url(self):
        """Test url() always returns local storage URL."""
        with patch(
            "django.core.files.storage.FileSystemStorage.url", return_value="/media/test.txt"
        ):
            result = self.storage.url("test.txt")

            self.assertEqual(result, "/media/test.txt")
            # Should not check fallback
            self.mock_fallback.exists.assert_not_called()

    def test_sync_handles_fallback_errors(self):
        """Test that errors during fallback sync are handled gracefully."""
        self.mock_fallback.exists.side_effect = OSError("Connection error")

        with (
            patch("django.core.files.storage.FileSystemStorage.exists", return_value=False),
            self.assertLogs("contentfiles.fallback_sync_storage", level="ERROR"),
        ):
            result = self.storage.exists("test.txt")

            self.assertFalse(result)

    def test_sync_without_fallback_storage(self):
        """Test that sync gracefully fails when no fallback is configured."""
        with self.assertLogs("contentfiles.fallback_sync_storage", level="WARNING"):
            storage = LocalFallbackSyncStorage()
        storage._fallback_storage = None

        with patch("django.core.files.storage.FileSystemStorage.exists", return_value=False):
            result = storage.exists("test.txt")

            self.assertFalse(result)
