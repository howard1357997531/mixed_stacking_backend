# Generated by Django 4.2.4 on 2023-09-25 01:39

from django.db import migrations, models
import mainapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0013_order_csv_file_alter_order_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='csv_file',
            field=models.FileField(blank=True, null=True, upload_to=mainapp.models.upload_to),
        ),
    ]
