import os
from datetime import timedelta
from os.path import join

import dj_database_url
import structlog
from configurations import Configuration
from django.core.exceptions import ImproperlyConfigured
from environs import Env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = Env()
env.read_env("service_config.env", recurse=False)

# ── structlog — configured once at import time ────────────────────────────────

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


class Common(Configuration):

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
        "djoser",
        "django_filters",
        "storages",
        "corsheaders",
        "djrichtextfield",
        "drf_spectacular",
        # papadam apps
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

    ALLOWED_HOSTS = ["*"]
    CORS_ORIGIN_ALLOW_ALL = True
    CORS_ALLOW_CREDENTIALS = True
    ROOT_URLCONF = "papadapi.urls"
    SECRET_KEY = env.str("DJANGO_SECRET_KEY")
    WSGI_APPLICATION = "papadapi.wsgi.application"

    # Email
    EMAIL_HOST = env.str("EMAIL_HOST", None)
    if not EMAIL_HOST:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    else:
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        EMAIL_PORT = env.str("EMAIL_PORT")
        EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "")
        EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "")

    ADMINS = (("papadam", "admin@papadam.local"),)

    # ── Database — PostgreSQL only ────────────────────────────────────────────

    _db_url = env.str("DB_URL")
    if _db_url.startswith("sqlite"):
        raise ImproperlyConfigured(
            "SQLite is not supported in papadam. "
            "Set DB_URL to a PostgreSQL connection string: "
            "postgres://user:password@host:5432/dbname"
        )
    DATABASES = {"default": dj_database_url.config(default=_db_url, conn_max_age=600)}

    # ── Redis ─────────────────────────────────────────────────────────────────

    REDIS_URL = env.str("REDIS_URL", "redis://redis:6379/0")

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }

    # ── ARQ task queue ────────────────────────────────────────────────────────

    ARQ_QUEUES = {
        "default": {
            "host": REDIS_URL,
        }
    }

    # ── General ───────────────────────────────────────────────────────────────

    APPEND_SLASH = True
    TIME_ZONE = "Asia/Kolkata"
    LANGUAGE_CODE = "en-us"
    USE_I18N = False
    USE_L10N = True
    USE_TZ = True
    LOGIN_REDIRECT_URL = "/"
    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

    # ── Static files ──────────────────────────────────────────────────────────

    STATIC_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), "staticassets"))
    STATICFILES_DIRS = [os.path.normpath(join(os.path.dirname(BASE_DIR), "static"))]
    STATIC_URL = "/static/"
    STATICFILES_FINDERS = (
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    )

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [os.path.normpath(join(os.path.dirname(BASE_DIR), "templates"))],
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

    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    # ── Logging — structlog handles formatting, Django routes to stdout ───────

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {"class": "logging.StreamHandler"},
        },
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        },
    }

    # ── Auth ──────────────────────────────────────────────────────────────────

    AUTH_USER_MODEL = "users.User"

    SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
        "ROTATE_REFRESH_TOKENS": True,
        "BLACKLIST_AFTER_ROTATION": False,
        "UPDATE_LAST_LOGIN": True,
        "ALGORITHM": "HS256",
        "AUTH_HEADER_TYPES": ("Bearer",),
        "USER_ID_FIELD": "id",
        "USER_ID_CLAIM": "user_id",
    }

    DJOSER = {
        "PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND": False,
        "USERNAME_RESET_SHOW_EMAIL_NOT_FOUND": False,
        "LOGOUT_ON_PASSWORD_CHANGE": True,
        "PASSWORD_RESET_CONFIRM_URL": "password/reset/confirm/{uid}/{token}",
        "SEND_CONFIRMATION_EMAIL": False,
        "ACTIVATION_URL": "activate/{uid}/{token}",
        "SEND_ACTIVATION_EMAIL": False,
        "TOKEN_MODEL": None,  # use simplejwt, not DRF opaque tokens
        "SERIALIZERS": {
            "current_user": "papadapi.users.serializers.UserMEApiSerializer",
            "user": "papadapi.users.serializers.UserMEApiSerializer",
        },
    }

    # ── DRF ───────────────────────────────────────────────────────────────────

    REST_FRAMEWORK = {
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "PAGE_SIZE": env.int("DJANGO_PAGINATION_LIMIT", 10),
        "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
        "DEFAULT_RENDERER_CLASSES": (
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",
        ),
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ),
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    }

    # ── OpenAPI (drf-spectacular) ─────────────────────────────────────────────

    SPECTACULAR_SETTINGS = {
        "TITLE": "papadam API",
        "DESCRIPTION": "Participatory Archive for Participatory Action",
        "VERSION": "1.0.0",
        "SERVE_INCLUDE_SCHEMA": False,
        "COMPONENT_SPLIT_REQUEST": True,
    }

    # ── Storage ───────────────────────────────────────────────────────────────

    # ── Internal service key — shared by transcribe worker ───────────────────

    INTERNAL_SERVICE_KEY = env.str("INTERNAL_SERVICE_KEY", "")

    # ── Storage ───────────────────────────────────────────────────────────────

    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

    STORAGE_TYPE = env.str("PAPAD_FILE_STORAGE_TYPE")
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_FILE_OVERWRITE = False
    AWS_STORAGE_BUCKET_NAME = env.str("PAPAD_STORAGE_BUCKET_NAME")

    if STORAGE_TYPE == "minio":
        AWS_ACCESS_KEY_ID = env.str("MINIO_ROOT_USER")
        AWS_SECRET_ACCESS_KEY = env.str("MINIO_ROOT_PASSWORD")
        AWS_S3_ENDPOINT_URL = env.str("MINIO_S3_ENDPOINT_URL")
        AWS_QUERYSTRING_AUTH = False
    else:
        AWS_ACCESS_KEY_ID = env.str("AWS_S3_ACCESS_KEY")
        AWS_S3_SECURE_URLS = True
        AWS_SECRET_ACCESS_KEY = env.str("AWS_S3_SECRET_KEY")
        AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL")
        AWS_QUERYSTRING_AUTH = False
        if env.str("AWS_S3_CUSTOM_DOMAIN", None) is not None:
            AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN")
        AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME")
