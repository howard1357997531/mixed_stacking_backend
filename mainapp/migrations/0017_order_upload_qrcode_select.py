# Generated by Django 4.2.4 on 2023-09-26 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0016_qrcodeexecute'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='upload_qrcode_select',
            field=models.BooleanField(default=False),
        ),
    ]
