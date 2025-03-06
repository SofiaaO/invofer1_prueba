# Generated by Django 5.0.7 on 2025-03-03 20:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producto',
            name='categoria',
        ),
        migrations.RemoveField(
            model_name='producto',
            name='estado',
        ),
        migrations.RemoveField(
            model_name='producto',
            name='fecha_registro',
        ),
        migrations.RemoveField(
            model_name='producto',
            name='marca',
        ),
        migrations.CreateModel(
            name='Producto_Marca_Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('estado', models.BooleanField(default=True)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='myapp.categoria')),
                ('marca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.marca')),
                ('nombre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.producto')),
            ],
        ),
    ]
