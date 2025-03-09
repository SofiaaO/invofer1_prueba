from django.shortcuts import render
from django.core.paginator import Paginator
from django.apps import apps
from django.contrib.auth.decorators import login_required
@login_required
def historial_general(request):
    modelos_auditados = [
        'Cliente', 'Proveedor', 'Marca', 'UnidadMedida', 'Categoria', 
        'Producto', 'Presentacion', 'Ventas', 'Compras', 'Impuesto', 'Movimiento', 
    ]

    registros = []
    for nombre_modelo in modelos_auditados:
        modelo = apps.get_model('myapp', nombre_modelo)
        historial_modelo = modelo.history.all()
        for registro in historial_modelo:
            if registro.history_type == '+':
                cambios = "Creación"
                detalles = "Objeto creado."
            elif registro.history_type == '~':
                cambios = "Modificación"

                if registro.prev_record:
                    diff = registro.diff_against(registro.prev_record)
                    detalles = []
                    for change in diff.changes:
                        detalles.append(f"{change.field}: {change.old} -> {change.new}")
                    detalles = "; ".join(detalles)
                else:
                    detalles = "Cambios no especificados."
            elif registro.history_type == '-':
                cambios = "Eliminación"
                detalles = "Objeto eliminado."
            else:
                cambios = registro.history_change_reason or "Cambio no especificado"
                detalles = "Cambios no especificados."

            if nombre_modelo == 'Ventas':
                id_objeto = registro.instance.id_venta
            elif nombre_modelo == 'Compras':
                id_objeto = registro.instance.id_compra
            else:
                id_objeto = registro.instance.id

            registros.append({
                'modelo': nombre_modelo,
                'fecha': registro.history_date,
                'usuario': registro.history_user,
                'cambios': cambios,
                'detalles': detalles,  
                'objeto': str(registro.instance),  
                'id_objeto': id_objeto,  
            })

    registros.sort(key=lambda x: x['fecha'], reverse=True)

    paginator = Paginator(registros, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    filtro_modelo = request.GET.get('modelo')
    if filtro_modelo:
        registros = [r for r in registros if r['modelo'] == filtro_modelo]
        paginator = Paginator(registros, 25)
        page_obj = paginator.get_page(page_number)

    return render(request, 'Auditorias/historial_generico.html', {
        'page_obj': page_obj,
        'modelos_auditados': modelos_auditados,
        'filtro_modelo': filtro_modelo,
    })