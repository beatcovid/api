import uuid

from django.db import models


class Respondent(models.Model):
    id = models.UUIDField(
        verbose_name="User uuid field",
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    submissions = models.IntegerField(
        verbose_name="User number of submissions", default=0
    )
    last_submission = models.DateTimeField(blank=True, null=True)
    last_login = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now=True)


class Session(models.Model):
    respondent = models.ForeignKey(
        Respondent, on_delete=models.DO_NOTHING, related_name="sessions"
    )
    # @TODO refactor this into a choices and value field so it can be grown by ID type
    # add expiry to each type
    cookie_id = models.CharField(
        max_length=256, verbose_name="User cookie ID", db_index=True, blank=True
    )
    # this is the browser fingerprint @TODO do we want to do this?
    browser_id = models.CharField(
        max_length=256, verbose_name="User brower ID", db_index=True, blank=True
    )
    device_id = models.CharField(
        max_length=256, verbose_name="User device ID", db_index=True, blank=True
    )


def default_expiry_date():
    from datetime import datetime, timedelta
    now = datetime.now()
    expiry = now + timedelta(minutes=20)
    return expiry

class TransitionAssistant(models.Model):
    respondent = models.ForeignKey('Respondent', models.DO_NOTHING)
    expires_at = models.DateTimeField(default=default_expiry_date)
    transfer_key = models.CharField(max_length=6, unique=True)
