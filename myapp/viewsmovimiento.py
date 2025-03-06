from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Movimiento, DetalleMovimiento, Presentacion
from .forms import MovimientoForm, DetalleMovimientoForm
from datetime import datetime

def listar_movimientos(request):
    # Obtener los parámetros de filtrado
    tipo_movimiento = request.GET.get('tipo_movimiento')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Filtrar los movimientos
    movimientos_list = DetalleMovimiento.objects.all().select_related('movimiento', 'presentacion')

    if tipo_movimiento:
        movimientos_list = movimientos_list.filter(movimiento__tipo_movimiento=tipo_movimiento)

    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        movimientos_list = movimientos_list.filter(movimiento__fecha_movimiento__range=[fecha_inicio, fecha_fin])

    presentaciones = Presentacion.objects.all()

    # Paginación
    paginator = Paginator(movimientos_list, 10)
    page = request.GET.get('page') 
    try:
        movimientos = paginator.page(page)
    except PageNotAnInteger:
        movimientos = paginator.page(1)
    except EmptyPage:
        movimientos = paginator.page(paginator.num_pages)

    if request.method == 'POST':
        form_movimiento = MovimientoForm(request.POST)
        form_detalle = DetalleMovimientoForm(request.POST)
        
        if form_movimiento.is_valid() and form_detalle.is_valid():
            movimiento = form_movimiento.save(commit=False)
            movimiento.usuario = request.user
            movimiento.fecha_movimiento = timezone.now()
            movimiento.save()

            detalle = form_detalle.save(commit=False)
            detalle.movimiento = movimiento
            detalle.subtotal = detalle.cantidad * detalle.precio_unitario
            detalle.save()

            movimiento.total = detalle.subtotal
            movimiento.save()

            presentacion = detalle.presentacion
            if movimiento.tipo_movimiento == 'ajuste_entrada':
                presentacion.stock += detalle.cantidad
            elif movimiento.tipo_movimiento == 'ajuste_salida':
                presentacion.stock -= detalle.cantidad
            presentacion.total_neto = presentacion.valor * presentacion.stock
            presentacion.save()

            messages.success(request, 'Movimiento registrado correctamente.')
            return redirect('listar_movimientos')
    else:
        form_movimiento = MovimientoForm()
        form_detalle = DetalleMovimientoForm()

    return render(request, 'movimientos/listar_movimientos.html', {
        'movimientos': movimientos,  
        'form_movimiento': form_movimiento,
        'form_detalle': form_detalle,
        'tipo_movimiento': tipo_movimiento,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'presentaciones': presentaciones
    })