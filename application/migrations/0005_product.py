# Generated by Django 5.0.7 on 2024-11-27 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0004_alter_profile_address_alter_profile_country'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=255)),
                ('item_description', models.TextField()),
                ('old_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('new_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('image', models.ImageField(upload_to='product_images/')),
            ],
        ),
    ]