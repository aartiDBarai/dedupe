# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-13 17:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_remove_status_pair_id'),
    ]

    operations = [
        migrations.DeleteModel(
            name='status',
        ),
    ]
