from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Categoria, AuditLog
from django.contrib.auth import get_user_model

""" @receiver(post_save, sender=Categoria)
def registrar_auditoria_categoria(sender, instance, created, **kwargs):
    if created:
        usuario = instance.usuario_creador  # Extraer usuario_creador de la categoría

        if not usuario:
            usuario = get_user_model().objects.first()  # Si no hay usuario, tomar uno de la BD

        AuditLog.objects.create(
            usuario=usuario,
            accion=f'Creación de categoría: {instance.nombre}',
            detalles=f'Categoría con ID {instance.id} fue creada.',
        ) """