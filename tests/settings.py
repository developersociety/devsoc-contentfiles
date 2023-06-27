import django

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

USE_TZ = True

SECRET_KEY = "contentfiles"

if django.VERSION >= (4, 2):
    STORAGES = {
        "default": {
            "BACKEND": "contentfiles.storage.MediaStorage",
        },
    }
else:
    DEFAULT_FILE_STORAGE = "contentfiles.storage.MediaStorage"

CONTENTFILES_PREFIX = "demo"
