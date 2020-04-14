# Generated by Django 3.0.4 on 2020-04-11 11:46

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Respondent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='User uuid field')),
                ('submissions', models.IntegerField(default=0, verbose_name='User number of submissions')),
                ('last_submission', models.DateTimeField(blank=True, null=True)),
                ('last_login', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cookie_id', models.CharField(blank=True, db_index=True, max_length=256, verbose_name='User cookie ID')),
                ('browser_id', models.CharField(blank=True, db_index=True, max_length=256, verbose_name='User brower ID')),
                ('device_id', models.CharField(blank=True, db_index=True, max_length=256, verbose_name='User device ID')),
                ('respondent', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='sessions', to='respondent.Respondent')),
            ],
        ),
    ]