from django.contrib import admin
from myapp.models import *
# Register your models here.
admin.site.register(Producto)
admin.site.register(Presentacion)
admin.site.register(Cliente)
admin.site.register(DetalleVentas)
admin.site.register(CustomUser)
admin.site.register(Ventas)
admin.site.register(Impuesto)
admin.site.register(Categoria)
admin.site.register(Producto_Marca_Categoria)
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'fecha', 'detalles')  # Muestra estos campos en el admin
    list_filter = ('usuario', 'accion', 'fecha')  # Filtros por usuario, acción y fecha
    search_fields = ('accion', 'detalles')  # Permite buscar por acción y detalles
    ordering = ('-fecha',)  # Ordenar por fecha (descendente)