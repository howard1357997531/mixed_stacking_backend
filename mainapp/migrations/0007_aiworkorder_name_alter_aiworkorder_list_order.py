# Generated by Django 4.2.4 on 2023-09-05 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0006_aiworkorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiworkorder',
            name='name',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='aiworkorder',
            name='list_order',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
