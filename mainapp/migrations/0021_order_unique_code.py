# Generated by Django 4.2.4 on 2023-10-19 02:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0020_delete_qrcodeexecute_remove_order_display_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='unique_code',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
