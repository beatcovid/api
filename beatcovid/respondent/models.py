from django.db import models

# @TODO custom user for auth or not?


# @TODO there is a better way to do this .. associate a list of
# auth token types against a user so they can have multiple devices
# and browsers
class Respondent(models.Model):
    uid = models.UUIDField(verbose_name="User uuid field", primary_key=True)
    cookie_id = models.CharField(max_length=256, verbose_name="User cookie ID")
    # this is the browser fingerprint @TODO do we want to do this?
    browser_id = models.CharField(max_length=256, verbose_name="User brower ID")
    device_id = models.CharField(max_length=256, verbose_name="User device ID")
    submissions = models.IntegerField(verbose_name="User number of submissions")
