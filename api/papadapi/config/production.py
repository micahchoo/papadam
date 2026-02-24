
from urllib.parse import urlparse

from environs import Env

from .common import Common

env = Env()
env.read_env("service_config.env", recurse=False)


class Production(Common):
    INSTALLED_APPS = Common.INSTALLED_APPS
    INSTALLED_APPS += ("gunicorn",)

    APP_ENV = env.str("DJANGO_APP_ENV", "production")

    # Extract hostname from PUBLIC_API_URL for ALLOWED_HOSTS / CSRF
    _public_api_url = env.str("PUBLIC_API_URL", "")
    APP_URL = urlparse(_public_api_url).hostname or "localhost"

    # Browser-visible URLs returned by /config.json to the SvelteKit SPA
    PUBLIC_API_URL = _public_api_url
    PUBLIC_CRDT_URL = env.str("PUBLIC_CRDT_URL", "")

    # Static shared secret for CRDT server → Django persistence API calls.
    # Must match CRDT_SERVER_TOKEN in deploy/service_config.env.
    # Not a JWT — never expires. Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    CRDT_SERVER_TOKEN = env.str("CRDT_SERVER_TOKEN", "")

    SENTRY_KEY = env.str("SENTRY_KEY", None)
    SENTRY_ENV = env.str("SENTRY_ENV", "production")

    if APP_ENV == "production":
        DEBUG = False
        ALLOWED_HOSTS = [APP_URL]

        # Restrict CORS to the configured public origin only
        CORS_ORIGIN_ALLOW_ALL = False
        CORS_ALLOWED_ORIGINS = [_public_api_url] if _public_api_url else []

        # Trust X-Forwarded-Proto from reverse proxy (NPM / Caddy / nginx)
        APP_HTTPS = env.bool("DJANGO_APP_HTTPS", True)
        if APP_HTTPS:
            SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
            CSRF_TRUSTED_ORIGINS = ["https://" + APP_URL]
        else:
            SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "http")
            CSRF_TRUSTED_ORIGINS = ["http://" + APP_URL]

        if SENTRY_KEY:
            import sentry_sdk

            sentry_sdk.init(
                dsn="https://" + SENTRY_KEY + ".ingest.de.sentry.io/4507826585862224",
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
                environment=SENTRY_ENV,
            )
