# Generated by Django 5.1.7 on 2025-04-11 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_telegramgroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramaccount',
            name='is_default',
            field=models.BooleanField(default=False),
        ),
    ]
