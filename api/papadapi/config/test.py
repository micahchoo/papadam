"""
Standalone test settings for pytest-django.

Does NOT inherit from Common — no external services required (no Postgres,
no Redis, no S3/MinIO).  SQLite in-memory + dummy cache + in-memory storage.
"""

from datetime import timedelta

# ── Core ──────────────────────────────────────────────────────────────────────

SECRET_KEY = "insecure-test-secret-key-do-not-use-in-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "papadapi.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
USE_I18N = False
USE_L10N = True

# ── Database ──────────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {"NAME": ":memory:"},
    }
}

# ── Caches ────────────────────────────────────────────────────────────────────

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

# ── Storage ───────────────────────────────────────────────────────────────────

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}
MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/papadam-test/"

# Internal service key — set per-test via pytest settings fixture when testing transcript endpoint
INTERNAL_SERVICE_KEY = ""

# Needed by archive app at import time even when using InMemoryStorage
AWS_STORAGE_BUCKET_NAME = "test-bucket"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"
AWS_S3_ENDPOINT_URL = "http://localhost:9000"

# ── Apps ──────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "djoser",
    "corsheaders",
    "djrichtextfield",
    "drf_spectacular",
    # papadam
    "papadapi.common",
    "papadapi.users",
    "papadapi.archive",
    "papadapi.annotate",
    "papadapi.importexport",
    "papadapi.events",
    "papadapi.crdt",
    "papadapi.exhibit",
    "papadapi.media_relation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ── Auth ──────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = "users.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_MODEL": None,
}

DJOSER = {
    "TOKEN_MODEL": None,
    "SERIALIZERS": {
        "current_user": "papadapi.users.serializers.UserMEApiSerializer",
        "user": "papadapi.users.serializers.UserMEApiSerializer",
    },
}

# ── DRF ───────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "anon": None,
        "user": None,
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "papadam API",
    "VERSION": "0.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── Rich text ─────────────────────────────────────────────────────────────────

DJRICHTEXTFIELD_SETTINGS: dict[str, object] = {}

# ── Static ────────────────────────────────────────────────────────────────────

STATIC_URL = "/static/"
