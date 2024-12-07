# Generated by Django 5.0.7 on 2024-11-25 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0002_profile_full_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='full_name',
        ),
        migrations.AddField(
            model_name='profile',
            name='fullname',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]