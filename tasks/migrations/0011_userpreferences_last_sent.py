# Generated by Django 3.2.12 on 2022-02-07 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_auto_20220204_0303'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpreferences',
            name='last_sent',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
