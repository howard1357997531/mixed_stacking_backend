# Generated by Django 4.2.4 on 2024-02-29 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0033_historyrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='historyrecord',
            name='reset_index',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
