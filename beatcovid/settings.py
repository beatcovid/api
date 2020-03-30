import os
from pathlib import Path
from pprint import pprint

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

env = environ.Env(DEBUG=(bool, False), USE_S3=(bool, False))

ENV = env.str("ENV", "development")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_FILE = f".env.{ENV}"
ENV_PATH = os.path.join(BASE_DIR, ENV_FILE)
if os.path.isfile(ENV_PATH):
    env.read_env(ENV_PATH)
    # environ.Env.read_env(env_file=)

# False if not in os.environ
DEBUG = env("DEBUG", default=True)
SECRET_KEY = env("SECRET_KEY")
SENTRY_DSN = env("SENTRY_DSN")

if SENTRY_DSN and (DEBUG == False):
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        environment=ENV,
        send_default_pii=True,
    )


ALLOWED_HOSTS = ["beatcovid19now.org", "127.0.0.10", "127.0.0.1", "localhost"]

ALLOWED_CLIENT_HOSTS = ALLOWED_HOSTS

CORS_ORIGIN_REGEX_WHITELIST = [
    r"https?://127\.0\.0\.\d+(:?\:\d{4})?",
    r"https://beatcovid19now.org",
]

# Application definition
INSTALLED_APPS = [
    # core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # local
    # third party
    # "django_extensions",
    "huey.contrib.djhuey",
    "rest_framework",
    "corsheaders",
    "storages",
    "bootstrapform",
    "survey",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "beatcovid.urls"


CSV_DIRECTORY = Path("csv")
TEX_DIRECTORY = Path("tex")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "beatcovid.wsgi.application"

DATABASES_AVAILABLE = {
    "production": env.db(),
    "development": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, ".db-development.sqlite3"),
    },
    "test": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, ".db-testing.sqlite3"),
    },
}

DB_USING = os.environ.get("DJANGO_DATABASE", "development")

if DB_USING not in DATABASES_AVAILABLE.keys():
    raise Exception(
        "{} is not one of the available databases. Select one of: {}".format(
            DB_USING, ", ".join(DATABASES_AVAILABLE.keys())
        )
    )

DATABASES = {"default": DATABASES_AVAILABLE[DB_USING]}


COUNTRIES_FIRST = ["AU", "NZ"]
# redis
REDIS_HOST = env("REDIS_HOST", default="127.0.0.6")
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.6:6379/")


from .scheduler import scheduler  # isort:skip pylint: disable=wrong-import-position

HUEY = scheduler

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "debug.log",
        },
        "console": {"class": "logging.StreamHandler", "level": "INFO"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        "beatcovid": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Email configuration

EMAIL_CONFIG = env.email_url("EMAIL_URL", default="smtp://127.0.0.6:1025")
vars().update(EMAIL_CONFIG)

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="beatcovid19now <no-reply@beatcovid19now.org>"
)


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-au"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

USE_S3 = os.getenv("USE_S3", default=False)

if USE_S3:
    # aws settings
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    # s3 static settings
    AWS_LOCATION = "static"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
else:
    STATIC_URL = "/staticfiles/"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

MEDIA_URL = "/mediafiles/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")
