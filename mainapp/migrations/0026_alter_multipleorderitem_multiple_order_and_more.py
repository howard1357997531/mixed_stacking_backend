# Generated by Django 4.2.4 on 2023-10-31 03:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0025_rename_orderid_list_multipleorder_orderselectid_str'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multipleorderitem',
            name='multiple_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='multiple_order', to='mainapp.multipleorder'),
        ),
        migrations.AlterField(
            model_name='multipleorderitem',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order', to='mainapp.order'),
        ),
    ]