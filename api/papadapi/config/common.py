import os
from os.path import join

import dj_database_url
from configurations import Configuration
from distutils.util import strtobool
from environs import Env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = Env()
env.read_env("service_config.env", recurse=False)


class Common(Configuration):

    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        # Third party apps
        "rest_framework",  # utilities for rest apis
        "rest_framework.authtoken",  # token authentication
        "djoser",  # Auth made easier
        "django_filters",  # for filtering rest endpoints
        "storages",
        "corsheaders",
        "djrichtextfield",
        "huey.contrib.djhuey",
        # Your apps
        "papadapi.common",
        "papadapi.users",
        "papadapi.archive",
        "papadapi.annotate",
        "papadapi.importexport",
        "papadapi.pages",
    ]

    # https://docs.djangoproject.com/en/2.0/topics/http/middleware/
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
    EMAIL_HOST = env.str("EMAIL_HOST",None)
    if not EMAIL_HOST:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        EMAIL_PORT = env.str("EMAIL_PORT")
        EMAIL_HOST_USER = env.str("EMAIL_HOST_USER","")
        EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD","")

    ADMINS = (("Author", "team@janastu.org"),)
    # Database
    DATABASES = {
        "default": dj_database_url.config(
            # default=str(env.str('DB_URL'))
            default=env.str("DB_URL")
        )
    }

    # General
    APPEND_SLASH = True
    TIME_ZONE = "Asia/Kolkata"
    LANGUAGE_CODE = "en-us"
    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    USE_I18N = False
    USE_L10N = True
    USE_TZ = True
    LOGIN_REDIRECT_URL = "/"

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/2.0/howto/static-files/
    STATIC_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), "staticassets"))
    STATICFILES_DIRS = [
        os.path.normpath(join(os.path.dirname(BASE_DIR), "static"))
        ]
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

    # Password Validation
    # https://docs.djangoproject.com/en/2.0/topics/auth/passwords/#module-django.contrib.auth.password_validation
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

    # Logging
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "django.server": {
                "()": "django.utils.log.ServerFormatter",
                "format": "[%(server_time)s] %(message)s",
            },
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
            },
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "filters": {
            "require_debug_true": {
                "()": "django.utils.log.RequireDebugTrue",
            },
        },
        "handlers": {
            "django.server": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "django.server",
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
            "mail_admins": {
                "level": "ERROR",
                "class": "django.utils.log.AdminEmailHandler",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "propagate": False,
            },
            "django.server": {
                "handlers": ["django.server"],
                "level": "INFO",
                "propagate": False,
            },
            "django.request": {
                "handlers": ["mail_admins", "console"],
                "level": "ERROR",
                "propagate": False,
            },
            "django.db.backends": {"handlers": ["console"], "level": "INFO"},
        },
    }

    # Custom user app
    AUTH_USER_MODEL = "users.User"

    DJOSER = {
        "PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND": False,
        "USERNAME_RESET_SHOW_EMAIL_NOT_FOUND": False,
        "LOGOUT_ON_PASSWORD_CHANGE": True,
        'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
        'SEND_CONFIRMATION_EMAIL': False,
        'ACTIVATION_URL': 'activate/{uid}/{token}',
        'SEND_ACTIVATION_EMAIL': False,
        'EMAIL': {
        'password_reset': 'djoser.email.PasswordResetEmail',
    },
        "SERIALIZERS": {
            # Overrides with custom api response
            "current_user": "papadapi.users.serializers.UserMEApiSerializer",
            "user": "papadapi.users.serializers.UserMEApiSerializer",
        },
    }

    # Django Rest Framework
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
            "rest_framework.authentication.TokenAuthentication",
        ),
    }

    # Storage config defaults

    # DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage" # Leave this unchanged
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage"
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
    STORAGE_TYPE = env.str("PAPAD_FILE_STORAGE_TYPE")

    # Sane AWS defaults for papad
    AWS_DEFAULT_ACL = "public-read" # TODO: How to handle this for AWS S3 based hosted storages ?
    AWS_S3_FILE_OVERWRITE = False
    AWS_STORAGE_BUCKET_NAME = env.str("PAPAD_STORAGE_BUCKET_NAME")
    
    if STORAGE_TYPE == "minio":
        AWS_ACCESS_KEY_ID = env.str("MINIO_ROOT_USER")
        AWS_SECRET_ACCESS_KEY = env.str("MINIO_ROOT_PASSWORD")
        AWS_S3_ENDPOINT_URL = env.str("MINIO_S3_ENDPOINT_URL")
        AWS_QUERYSTRING_AUTH = False # In default minio case, remove query parameter authentication from generated URLs since the bucket is assumed to be public

    else: # Handle S3
        AWS_ACCESS_KEY_ID = env.str("AWS_S3_ACCESS_KEY")
        AWS_S3_SECURE_URLS = True # TODO: Debug what this flag impact is
        AWS_SECRET_ACCESS_KEY = env.str("AWS_S3_SECRET_KEY")
        AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL")
        AWS_QUERYSTRING_AUTH = False # In default minio case, remove query parameter authentication from generated URLs since the bucket is assumed to be public
        if env.str("AWS_S3_CUSTOM_DOMAIN", None) is not None:
            AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN")
        AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME")
        # GZIP_CONTENT_TYPES = "audio/mpeg,audio/x-ms-wma,audio/vnd.rn-realaudio,audio/x-wav,video/mpeg,video/mp4,video/quicktime,video/x-ms-wmv,video/x-msvideo,video/x-flv,video/webm"
        # AWS_IS_GZIPPED = True
    ## Background tasks

    HUEY = {
        "huey_class": "huey.SqliteHuey",  # Huey implementation to use.
        "name": DATABASES["default"]["NAME"],  # Use db name for huey.
        "filename": BASE_DIR + "/tasks.db",
        "results": False,  # Store return values of tasks.
        "store_none": False,  # If a task returns None, do not save to results.
        "immediate": False,  # If DEBUG=True, run synchronously.
        "utc": True,  # Use UTC for all times internally.
        "journal_mode": "delete",
        "consumer": {
            "workers": 1,
            "worker_type": "process",
            "initial_delay": 0.1,  # Smallest polling interval, same as -d.
            "backoff": 1.15,  # Exponential backoff using this rate, -b.
            "max_delay": 10.0,  # Max possible polling interval, -m.
            "scheduler_interval": 1,  # Check schedule every second, -s.
            "periodic": False,  # Enable crontab feature.
            "check_worker_health": True,  # Enable worker health checks.
            "health_check_interval": 1,  # Check worker health every second.
        },
    }
