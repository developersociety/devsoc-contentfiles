DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

SECRET_KEY = "contentfiles"

DEFAULT_FILE_STORAGE = "contentfiles.storage.MediaStorage"

CONTENTFILES_PREFIX = "demo"
