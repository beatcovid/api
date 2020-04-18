

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

SESSION_COOKIE_SECURE = True

SENTRY_DSN = "https://6330206ccb7f40dfa6d9ef63174f96ba@o368785.ingest.sentry.io/5204925"

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[DjangoIntegration()],
    environment="production",
    send_default_pii=True,
)

from .base import *  # isort:skip
