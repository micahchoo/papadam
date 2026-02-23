import os

from .common import Common

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Local(Common):
    DEBUG = True

    # Testing
    SECRET_KEY = "local"
    INSTALLED_APPS = Common.INSTALLED_APPS + [
        #"silk",
        ]

    # Mail

    # MEDIA_URL = f'http://minio1:9000/{AWS_STORAGE_BUCKET_NAME}/'
    #MIDDLEWARE = Common.MIDDLEWARE + ["silk.middleware.SilkyMiddleware"]
