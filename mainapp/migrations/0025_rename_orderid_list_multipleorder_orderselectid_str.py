# Generated by Django 4.2.4 on 2023-10-30 07:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0024_rename_order_list_multipleorder_orderid_list'),
    ]

    operations = [
        migrations.RenameField(
            model_name='multipleorder',
            old_name='orderId_list',
            new_name='orderSelectId_str',
        ),
    ]