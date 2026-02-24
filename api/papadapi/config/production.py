
import sentry_sdk
from environs import Env

from .common import Common

env = Env()
env.read_env("service_config.env", recurse=False)


class Production(Common):
    INSTALLED_APPS = Common.INSTALLED_APPS
    # Site
    # https://docs.djangoproject.com/en/2.0/ref/settings/#allowed-hosts
    INSTALLED_APPS += ("gunicorn",)
    APP_ENV = env.str("DJANGO_APP_ENV", "Production")
    APP_HTTPS = env.bool("DJANGO_APP_HTTPS", "Production")
    APP_URL = env.str("API_URL", None)
    SENTRY_KEY = env.str("SENTRY_KEY", None)
    SENTRY_ENV = env.str("SENTRY_ENV", "production")
    if APP_ENV == "production":
        DEBUG = False
        ALLOWED_HOSTS = [APP_URL]
        if APP_HTTPS:
            SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
            CSRF_TRUSTED_ORIGINS = ["https://"+APP_URL]
        else:
            SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'http')
            CSRF_TRUSTED_ORIGINS = ["http://"+APP_URL]
        if SENTRY_KEY:
            sentry_sdk.init(
            dsn="https://"+SENTRY_KEY+".ingest.de.sentry.io/4507826585862224",
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for tracing.
            traces_sample_rate=1.0,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=1.0,
            environment=SENTRY_ENV,
            )

