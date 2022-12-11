# Generated by Django 2.2.16 on 2022-12-11 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_follow'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('author', 'user'), name='check_unique_author_user'),
        ),
    ]
