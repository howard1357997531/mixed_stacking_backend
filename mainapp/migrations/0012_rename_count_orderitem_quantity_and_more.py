# Generated by Django 4.2.4 on 2023-09-24 11:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0011_order_aitraining_state'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderitem',
            old_name='count',
            new_name='quantity',
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orderItem', to='mainapp.order'),
        ),
    ]
