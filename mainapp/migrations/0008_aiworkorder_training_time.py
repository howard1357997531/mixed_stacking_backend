# Generated by Django 4.2.4 on 2023-09-06 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0007_aiworkorder_name_alter_aiworkorder_list_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiworkorder',
            name='training_time',
            field=models.FloatField(default=0),
        ),
    ]
