# Generated by Django 4.2.4 on 2023-09-18 05:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0009_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('width', models.CharField(blank=True, max_length=255, null=True)),
                ('height', models.CharField(blank=True, max_length=255, null=True)),
                ('depth', models.CharField(blank=True, max_length=255, null=True)),
                ('count', models.PositiveIntegerField(default=0)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mainapp.order')),
            ],
        ),
    ]
