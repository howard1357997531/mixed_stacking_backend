# Generated by Django 4.2.4 on 2023-10-30 07:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0022_multipleorder_multipleorderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='multipleorderitem',
            name='multiple_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mainapp.multipleorder'),
        ),
    ]
