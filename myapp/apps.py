from django.apps import AppConfig
from django.db.models.signals import post_migrate

def crear_grupos(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission

    grupos_permisos = {
        "Administrador": Permission.objects.all(),
        "Cajero": Permission.objects.filter(codename__in=[
            "view_ventas", "add_ventas", "view_cliente", "add_cliente", "change_cliente",
            "view_detalleventas", "add_detalleventas", "change_detalleventas"
        ]),
        "Almacen": Permission.objects.filter(codename__in=[
            "view_producto", "add_producto", "change_producto", "view_presentacion",
            "add_presentacion", "change_presentacion", "view_unidadmedida", "view_marca",
            "view_categoria", "view_categoriaunidadmedida"
        ]),
    }

    for nombre_grupo, permisos in grupos_permisos.items():
        grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
        grupo.permissions.set(permisos)

    print("Grupos y permisos creados correctamente.")


def crear_monedas_y_tasa_cambio(sender, **kwargs):

    from .models import Moneda, TasaCambio  
    usd, _ = Moneda.objects.get_or_create(
        codigo='USD',
        defaults={
            'nombre': 'Dólar Estadounidense',
            'simbolo': '$',
            'estado': True
        }
    )

    bs, _ = Moneda.objects.get_or_create(
        codigo='VES',
        defaults={
            'nombre': 'Bolívar Soberano',
            'simbolo': 'Bs',
            'estado': True
        }
    )
    TasaCambio.objects.get_or_create(
        moneda_origen=usd,
        moneda_destino=bs,
        defaults={'tasa': 1.0}  # Tasa de cambio predeterminada
    )

class MyAppConfig(AppConfig):
    name = 'myapp'

    def ready(self):
        # Conectamos ambas funciones a la señal post_migrate
        post_migrate.connect(crear_grupos, sender=self)
        post_migrate.connect(crear_monedas_y_tasa_cambio, sender=self)