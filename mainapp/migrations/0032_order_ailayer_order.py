# Generated by Django 4.2.4 on 2024-01-22 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0031_multipleorder_is_today_latest'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='aiLayer_order',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
