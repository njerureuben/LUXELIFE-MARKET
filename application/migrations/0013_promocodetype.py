# Generated by Django 5.0.7 on 2024-12-06 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0012_cart_cartitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromoCodeType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
