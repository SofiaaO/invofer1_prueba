# Generated by Django 5.1.5 on 2025-03-04 21:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_alter_movimiento_total'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='compras',
            name='estado',
        ),
        migrations.RemoveField(
            model_name='ventas',
            name='estado',
        ),
    ]
