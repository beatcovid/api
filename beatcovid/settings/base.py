import logging
import os

import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.django import DjangoIntegration

from ..utils import skip_site_packages_logs
from .environ import env, load_environment

logger = logging.getLogger("beatcovid.settings")
logger.setLevel(logging.INFO)
logger.propagate = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENV = env("ENV", default="development")
DEBUG = env("DEBUG", default=True)

ENV_PATH = os.path.join(BASE_DIR, f".env.{ENV}")

if os.path.isfile(ENV_PATH):
    print(f"Loading env from {ENV_PATH}")
    load_dotenv(dotenv_path=ENV_PATH)


# False if not in os.environ
DEBUG = env("DEBUG", default=True)

SECRET_KEY = env("SECRET_KEY")
SENTRY_DSN = env("SENTRY_DSN", default=None)

logger.info("DEBUG is set to {}".format(DEBUG))

if SENTRY_DSN and (DEBUG == False):
    logger.info("Setting sentry to {}".format(SENTRY_DSN))
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=ENV,
        send_default_pii=True,
    )
else:
    logger.warn("Sentry has not been set")

ALLOWED_HOSTS = [
    "api.beatcovid19now.org",
    "api.beatcov-staging.com",
    "api.beatcovid.test",
    "api.beatcov.org",
    "api.stopcovid.infotorch.org",
    "127.0.0.1",
    "localhost",
]

ALLOWED_CLIENT_HOSTS = ALLOWED_HOSTS

CORS_ORIGIN_REGEX_WHITELIST = [
    r"https://beatcovid19now.org",
    r"https://beatcovid.test",
    r"https://beatcov-staging.com",
    r"https://beatcov.org",
    r"https://stopcovid.infotorch.org",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-device-id",
    "x-uid",
]

CORS_ALLOW_METHODS = [
    "GET",
    "OPTIONS",
    "POST",
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
    "beatcovid",
    "beatcovid.intl",
    "beatcovid.api",
    "beatcovid.respondent",
    "beatcovid.symtracker",
    # third party
    "countries_plus",
    "languages_plus",
    # "django_extensions",
    "huey.contrib.djhuey",
    "rest_framework",
    "corsheaders",
    "storages",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "beatcovid.intl.middleware.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "beatcovid.urls"

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

# Kobo setup
KOBO_FORM_SERVER = env(
    "KOBO_FORM_SERVER", default="https://kobo.stopcovid.infotorch.org/"
)

# @TODO replace with restricted permission tokens
KOBO_FORM_TOKEN = env(
    "KOBO_FORM_TOKEN", default="867efc167553ff10d9a80beb988dfed9a282d07f"
)

KOBOCAT_API = env("KOBOCAT_API", default="https://kc.stopcovid.infotorch.org/")

# @TODO replace with restricted permission tokens
KOBOCAT_CREDENTIALS = env(
    "KOBOCAT_CREDENTIALS", default="c3VwZXJfYWRtaW46WkxOJEM3WTh6WA=="
)

SUBMISSION_COUNT_BASE = env("SUBMISSION_COUNT_BASE", default=18624)

RESPONDENT_COUNT_BASE = env("RESPONDENT_COUNT_BASE", default=18624)


# auth methods
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        # @TODO we'll proably need this
        # "rest_framework.authtoken",
    ]
}

# session cookie settings
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_SAMESITE = None
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365 * 5  # 5 years

# this dumb two-step is because setting the env as "None" doesn't cast as Python None
COOKIE_DOMAIN = env("COOKIE_DOMAIN", default=None)
if COOKIE_DOMAIN != None:
    SESSION_COOKIE_DOMAIN = COOKIE_DOMAIN.strip('"')

SESSION_COOKIE_NAME = "sid"

# should set this in prod

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

DB_USING = os.environ.get("DJANGO_DATABASE", ENV)

if DB_USING not in DATABASES_AVAILABLE.keys():
    raise Exception(
        "{} is not one of the available databases. Select one of: {}".format(
            DB_USING, ", ".join(DATABASES_AVAILABLE.keys())
        )
    )

DATABASES = {"default": DATABASES_AVAILABLE[DB_USING]}

logger.info("Using database {}".format(DB_USING))

COUNTRIES_FIRST = ["AU", "NZ"]

# redis
REDIS_HOST = env("REDIS_HOST", default="127.0.0.6")
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.10:6379/")

# mongo
MONGO_HOST = env("MONGO_HOST", default="mongodb://127.0.0.1/")

from ..scheduler import scheduler  # isort:skip pylint: disable=wrong-import-position

HUEY = scheduler

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "error.log",
        },
        "console": {"class": "logging.StreamHandler", "level": "DEBUG"},
    },
    "skip_site_packages_logs": {
        "()": "django.utils.log.CallbackFilter",
        "callback": skip_site_packages_logs,
    },
    "loggers": {
        "django": {"handlers": ["file"], "level": "INFO", "propagate": True},
        "django.utils.autoreload": {"level": "INFO",},
        "beatcovid": {"handlers": ["file"], "level": "INFO", "propagate": True},
    },
}

if DEBUG == True:
    logging.info("Setting debug loggers")
    LOGGING["loggers"]["django"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }
    LOGGING["loggers"]["beatcovid"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
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
LANGUAGE_CODE = "en"
LANGUAGE_COOKIE_DOMAIN = COOKIE_DOMAIN
LANGUAGE_COOKIE_NAME = "locale"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


LOKALISE_TOKEN = os.getenv("LOKALISE_TOKEN", default=None)
LOKALISE_PROJECT_ID = os.getenv(
    "LOKALISE_PROJECT_ID", default="588298865e9f9f91e6f251.37381743"
)

LOCALE_PATHS = [BASE_DIR + "/beatcovid/locale"]

# Static files (CSS, JavaScript, Images)
USE_S3 = os.getenv("USE_S3", default=False)

if USE_S3:
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")

    logger.info(
        "Setting up S3 for static hosting with bucket {}".format(AWS_STORAGE_BUCKET_NAME)
    )
    # aws settings
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    # s3 static settings
    AWS_LOCATION = "static"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
else:
    logger.info("Using local static files")
    STATIC_URL = "/staticfiles/"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

MEDIA_URL = "/mediafiles/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")
