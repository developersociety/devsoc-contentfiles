import logging

from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class LocalFallbackSyncStorage(FileSystemStorage):
    """
    A storage backend that uses local FileSystemStorage but falls back to a remote
    storage backend (e.g., S3 via contentfiles) to fetch missing files on-demand.

    Files fetched from the fallback are copied locally so subsequent accesses are fast.
    All write operations only affect local storage, never the remote fallback.

    Configuration:
    STORAGES = {
        "default": {
            "BACKEND": "contentfiles.fallback_sync_storage.LocalFallbackSyncStorage",
            "OPTIONS": {
                "fallback": "contentfiles.storage.MediaStorage"
            }
        }
    }
    """

    def __init__(self, **kwargs):
        fallback_backend = kwargs.pop("fallback", None)
        super().__init__(**kwargs)

        self._fallback_storage = None
        if fallback_backend:
            self._fallback_storage = self._initialize_fallback_storage(fallback_backend)
        else:
            logger.warning(
                "LocalFallbackSyncStorage initialized without a fallback backend. "
                "Files not found locally will raise errors."
            )

        # Used to prevent infinite exists/sync loops:
        self.local_exists_shortcircuit_cache = {}

    def _initialize_fallback_storage(self, fallback_backend):
        """
        Initialize the fallback storage backend from a dotted django import-path string.
        """
        try:
            storage_class = import_string(fallback_backend)
            return storage_class()
        except (ImportError, AttributeError) as e:
            error_msg = f"Could not import fallback storage backend '{fallback_backend}': {e}"
            raise ImproperlyConfigured(error_msg) from e

    def _sync_from_fallback(self, name):
        """
        Attempt to fetch a file from the fallback storage and save it locally.
        Returns True if successful, False otherwise.
        """

        if not self._fallback_storage:
            return False

        try:
            if not self._fallback_storage.exists(name):
                logger.debug("File '%s' not found in fallback storage either.", name)
                self.local_exists_shortcircuit_cache[name] = False
                return False

            logger.info("Fetching '%s' from fallback storage...", name)

            with self._fallback_storage.open(name, "rb") as fallback_file:
                # Save it to local storage using parent class save method
                # Use super() to avoid recursion and write directly to local storage
                self.local_exists_shortcircuit_cache[name] = False
                super().save(name, fallback_file)

            logger.info("Successfully synced '%s' from fallback to local storage.", name)
            self.local_exists_shortcircuit_cache[name] = True
        except OSError:
            logger.exception("Failed to sync '%s' from fallback storage", name)
            return False
        else:
            return True

    def exists(self, name):
        """
        Check if a file exists locally. If not, check fallback and sync if found.
        """

        cached = self.local_exists_shortcircuit_cache.get(name)
        if cached is not None:
            return cached

        if super().exists(name):
            return True

        return self._sync_from_fallback(name)

    def open(self, name, mode="rb"):
        """
        Open a file. If it doesn't exist locally, try to fetch from fallback first.
        """
        # For write modes, just use local storage
        if "w" in mode or "a" in mode:
            return super().open(name, mode)

        # For read modes, ensure file exists locally (sync if needed)
        if not super().exists(name):
            self._sync_from_fallback(name)

        # Now open from local storage
        return super().open(name, mode)

    def size(self, name):
        """
        Return the size of a file. Sync from fallback if not local.
        """
        if not super().exists(name):
            self._sync_from_fallback(name)

        return super().size(name)

    def url(self, name):
        """
        Return the URL for a file. Always use local storage URL.
        """
        # Even if file doesn't exist locally yet, return local URL
        # The file will be synced when actually accessed
        return super().url(name)

    def get_accessed_time(self, name):
        """
        Return the last accessed time. Sync from fallback if not local.
        """
        if not super().exists(name):
            self._sync_from_fallback(name)

        return super().get_accessed_time(name)

    def get_created_time(self, name):
        """
        Return the creation time. Sync from fallback if not local.
        """
        if not super().exists(name):
            self._sync_from_fallback(name)

        return super().get_created_time(name)

    def get_modified_time(self, name):
        """
        Return the last modified time. Sync from fallback if not local.
        """
        if not super().exists(name):
            self._sync_from_fallback(name)

        return super().get_modified_time(name)

    def save(self, name, content, max_length=None):
        """
        Save a file to local storage only. Never write to fallback.
        """
        # Always save to local storage, never to fallback
        return super().save(name, content, max_length=max_length)

    def delete(self, name):
        """
        Delete a file from local storage only. Never delete from fallback.
        """
        # This is intentional - we don't want local operations affecting production
        return super().delete(name)
