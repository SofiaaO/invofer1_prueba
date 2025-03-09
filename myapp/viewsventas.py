import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Max
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
import json
from myapp.forms import ClienteForm
from .models import DetalleMovimiento, Impuesto, Moneda, Movimiento, TasaCambio, Ventas, DetalleVentas, Presentacion, Cliente
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from django.contrib.auth.decorators import login_required
@login_required
def listar_ventas(request):
    query = request.GET.get('buscar', '')
    fecha = request.GET.get('fecha', '')

    ventas = Ventas.objects.all()

    if query:
        ventas = ventas.filter(
            Q(numero_factura__istartswith=query) | Q(cliente__nombre__istartswith=query)
        )

    if fecha:
        ventas = ventas.filter(fecha_venta__date=fecha)

    return render(request, 'Ventas/ventas_list.html', {'ventas': ventas})

@login_required
# REGISTRAR NUEVA VENTA
@login_required
def nueva_venta(request):
    if 'carrito' not in request.session:
        request.session['carrito'] = []

    carrito = request.session['carrito']
    monedas = Moneda.objects.exclude(codigo='VES')

    # Obtener la moneda seleccionada (por defecto, USD)
    moneda_seleccionada = request.session.get('moneda_seleccionada', 'USD')

    # Obtener el símbolo de la moneda seleccionada
    moneda_obj = Moneda.objects.filter(codigo=moneda_seleccionada).first()
    simbolo_moneda = moneda_obj.simbolo if moneda_obj else '$'

    # Obtener la tasa de cambio para la moneda seleccionada a bolívares
    tasa_cambio = TasaCambio.objects.filter(
        moneda_origen__codigo=moneda_seleccionada,
        moneda_destino__codigo='VES'
    ).order_by('-fecha').first()

    if tasa_cambio:
        tasa = float(tasa_cambio.tasa)
    else:
        tasa = 0  # Si no hay tasa de cambio, usar 0

    # Calcular el total en la moneda seleccionada y en bolívares
    total = sum(item['cantidad'] * item['precio'] for item in carrito)
    total_bs = total * tasa

    # Obtener el impuesto activo
    impuesto_activo = Impuesto.objects.filter(estado=True).first()
    if impuesto_activo:
        porcentaje_impuesto = float(impuesto_activo.porcentaje)
        impuesto = (total * porcentaje_impuesto) / 100  # Calcular el impuesto
        impuesto_bs = impuesto * tasa  # Calcular el impuesto en bolívares
    else:
        impuesto = 0  # Si no hay impuesto activo, usar 0
        impuesto_bs = 0  # Asegurar que el impuesto en bolívares sea 0

    total_con_impuesto = total + impuesto  # Total con impuesto incluido
    total_con_impuesto_bs = total_con_impuesto * tasa  # Total en bolívares con impuesto

    # Filtrar presentaciones activas
    presentaciones = Presentacion.objects.filter(estado=True)
    clientes = Cliente.objects.all()

    last_factura = Ventas.objects.aggregate(Max('numero_factura'))
    last_number = last_factura['numero_factura__max']
    numero_factura = str(int(last_number) + 1).zfill(6) if last_number else '000001'

    current_date = timezone.now().strftime('%d-%m-%Y') 

    return render(request, 'Ventas/ventas.html', {
        'presentaciones': presentaciones,
        'carrito': carrito,
        'total': total,
        'total_bs': total_bs,
        'total_con_impuesto': total_con_impuesto,
        'total_con_impuesto_bs': total_con_impuesto_bs,
        'impuesto': impuesto,
        'impuesto_bs': impuesto_bs,  # Pasar el impuesto en bolívares
        'impuesto_activo': impuesto_activo,  # Pasar el impuesto activo
        'clientes': clientes,
        'current_date': current_date,
        'numero_factura': numero_factura,
        'monedas': monedas,
        'moneda_seleccionada': moneda_seleccionada,
        'simbolo_moneda': simbolo_moneda,
        'tasa': tasa_cambio
    })


@login_required
# EDITAR CANTIDAD EN EL CARRITO
@login_required
def editar_cantidad_ventas(request):
    if request.method == "POST":
        id_presentacion = request.POST.get("id")
        nueva_cantidad = int(request.POST.get("cantidad", 1))  # Nueva cantidad
        carrito = request.session.get('carrito', [])

        # Obtener la presentación desde la base de datos
        presentacion = get_object_or_404(Presentacion, pk=id_presentacion)
        moneda_seleccionada = request.session.get('moneda_seleccionada', 'USD')

        # Obtener la tasa de cambio para la moneda seleccionada a bolívares
        tasa_cambio = TasaCambio.objects.filter(
            moneda_origen__codigo=moneda_seleccionada,
            moneda_destino__codigo='VES'
        ).order_by('-fecha').first()

        if not tasa_cambio:
            return JsonResponse({"success": False, "error": "No se encontró una tasa de cambio válida para la moneda seleccionada."})

        tasa = float(tasa_cambio.tasa)

        # Buscar el producto en el carrito
        for item in carrito:
            if item['id'] == int(id_presentacion):
                # Validar que la nueva cantidad no supere el stock disponible
                if nueva_cantidad > presentacion.stock:
                    return JsonResponse({
                        "success": False,
                        "error": f"No hay suficiente stock disponible. Stock actual: {presentacion.stock}"
                    })

                # Actualizar la cantidad y el subtotal
                item['cantidad'] = nueva_cantidad
                item['subtotal'] = item['cantidad'] * item['precio']
                item['subtotal_bs'] = item['subtotal'] * tasa  # Actualizar subtotal en Bs
                subtotal_actualizado = item['subtotal']  
                subtotal_bs_actualizado = item['subtotal_bs']  # Subtotal en Bs actualizado
                break

        request.session['carrito'] = carrito

        # Calcular el total
        total = sum(item['cantidad'] * item['precio'] for item in carrito)
        total_bs = total * tasa  # Total en Bs

        # Obtener el impuesto activo
        impuesto_activo = Impuesto.objects.filter(estado=True).first()
        if impuesto_activo:
            porcentaje_impuesto = float(impuesto_activo.porcentaje)
            impuesto = (total * porcentaje_impuesto) / 100  # Calcular el impuesto
            impuesto_bs = impuesto * tasa  # Calcular el impuesto en bolívares
        else:
            impuesto = 0  # Si no hay impuesto activo, usar 0
            impuesto_bs = 0

        total_con_impuesto = total + impuesto  # Total con impuesto incluido
        total_con_impuesto_bs = total_con_impuesto * tasa  # Total en bolívares con impuesto

        return JsonResponse({
            "success": True,
            "cantidad": nueva_cantidad,
            "subtotal": subtotal_actualizado,  
            "subtotal_bs": subtotal_bs_actualizado,  # Subtotal en Bs
            "total": total,
            "total_bs": total_bs,  # Total en Bs
            "impuesto": impuesto,  # Impuesto en dólares
            "impuesto_bs": impuesto_bs,  # Impuesto en bolívares
            "impuesto_nombre": impuesto_activo.nombre if impuesto_activo else "N/A",  # Nombre del impuesto
            "impuesto_porcentaje": impuesto_activo.porcentaje if impuesto_activo else 0,  # Porcentaje del impuesto
            "total_con_impuesto": total_con_impuesto,  # Total con impuesto en dólares
            "total_con_impuesto_bs": total_con_impuesto_bs  # Total con impuesto en bolívares
        })

    return JsonResponse({"success": False, "error": "Solicitud inválida"})
# AGREGAR PRESENTACIÓN AL CARRITO
from django.shortcuts import redirect

@login_required
def agregar_producto(request):
    if request.method == 'POST':
        id_presentacion = request.POST['id_presentacion']
        cantidad = int(request.POST['cantidad'])

        moneda_seleccionada = request.session.get('moneda_seleccionada', 'USD')

        # Obtener la tasa de cambio para la moneda seleccionada a bolívares
        tasa_cambio = TasaCambio.objects.filter(
            moneda_origen__codigo=moneda_seleccionada,
            moneda_destino__codigo='VES'
        ).order_by('-fecha').first()

        if not tasa_cambio:
            raise ValueError("No se encontró una tasa de cambio válida para la moneda seleccionada.")

        tasa = float(tasa_cambio.tasa)

        if "cliente_id" in request.POST:
            request.session["cliente_id"] = request.POST["cliente_id"]

        presentacion = get_object_or_404(Presentacion, pk=id_presentacion)

        # Validar stock
        if cantidad > presentacion.stock:
            # Aquí puedes agregar un mensaje de error si lo deseas
            return redirect('nueva_venta')  # Redirige de vuelta al carrito

        carrito = request.session.get('carrito', [])

        for item in carrito:
            if item['id'] == presentacion.id:
                # Validar stock acumulado
                if item['cantidad'] + cantidad > presentacion.stock:
                    return redirect('nueva_venta')  
                item['cantidad'] += cantidad
                item['subtotal'] = item['cantidad'] * float(presentacion.precio_venta)
                item['subtotal_bs'] = item['subtotal'] * tasa
                break
        else:
            carrito.append({
                'id': presentacion.id,
                'codigo': presentacion.codigo,
                'nombre': f"{presentacion.producto.nombre} ({presentacion.producto.marca}) - {presentacion.valor} {presentacion.categoria_unidad.unidad_medida.abreviatura}",
                'cantidad': cantidad,
                'precio': float(presentacion.precio_venta),
                'precio_bs': float(presentacion.precio_venta) * tasa,  # Precio unitario en Bs
                'subtotal': cantidad * float(presentacion.precio_venta),
                'subtotal_bs': cantidad * float(presentacion.precio_venta) * tasa,  # Subtotal en Bs
            })

        request.session['carrito'] = carrito

        return redirect('nueva_venta')  # Redirige al carrito después de agregar el producto


@login_required
# ELIMINAR PRODUCTO DEL CARRITO
def eliminar_producto(request):
    if request.method == 'POST':
        id_producto = int(request.POST['id_producto'])
        carrito = request.session.get('carrito', [])
        carrito = [item for item in carrito if item['id'] != id_producto]
        request.session['carrito'] = carrito

        return redirect('nueva_venta')

@login_required
# GUARDAR VENTA
@login_required
def guardar_venta(request):
    if request.method == 'POST':
        try:
            cliente_id = request.POST['cliente_id']
            cliente = get_object_or_404(Cliente, cedula=cliente_id)

            moneda_seleccionada = request.session.get('moneda_seleccionada', 'USD')

            tasa_cambio = TasaCambio.objects.filter(
                moneda_origen__codigo=moneda_seleccionada,
                moneda_destino__codigo='VES'
            ).order_by('-fecha').first()

            if tasa_cambio:
                tasa = float(tasa_cambio.tasa)
            else:
                tasa = 0 

            last_factura = Ventas.objects.aggregate(Max('numero_factura'))
            last_number = last_factura['numero_factura__max']
            numero_factura = str(int(last_number) + 1).zfill(6) if last_number else '000001'

            if 'carrito' not in request.session:
                return JsonResponse({
                    'success': False,
                    'error': 'El carrito no está inicializado.'
                })

            carrito = request.session['carrito']
            total = sum(item['cantidad'] * item['precio'] for item in carrito)

            # Obtener el impuesto activo
            impuesto_activo = Impuesto.objects.filter(estado=True).first()
            if impuesto_activo:
                porcentaje_impuesto = float(impuesto_activo.porcentaje)
                impuesto = (total * porcentaje_impuesto) / 100  # Calcular el impuesto
            else:
                impuesto = 0  # Si no hay impuesto activo, usar 0

            total_con_impuesto = total + impuesto  # Total con impuesto incluido
            total_bs = total_con_impuesto * tasa  # Total en bolívares con impuesto

            venta = Ventas.objects.create(
                numero_factura=numero_factura,
                cliente=cliente,
                total=total_con_impuesto,
                total_bs=total_bs,
                impuesto=impuesto  # Guardar el impuesto en la venta
            )

            movimiento = Movimiento.objects.create(
                tipo_movimiento='venta',
                fecha_movimiento=timezone.now(),
                usuario=request.user,
                cliente=cliente,
                total=total_con_impuesto,
                descripcion=f"Venta realizada con factura {numero_factura}"
            )

            alertas_stock_minimo = []  # Lista para almacenar alertas de stock mínimo

            for item in carrito:
                subtotal = item['cantidad'] * item['precio']
                subtotal_bs = subtotal * tasa  # Calcular el subtotal en bolívares

                # Guardar en DetalleVentas
                DetalleVentas.objects.create(
                    venta=venta,
                    presentacion_id=item['id'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'],
                    precio_unitario_bs=item['precio'] * tasa,
                    subtotal=subtotal,
                    subtotal_bs=subtotal_bs
                )
                
                DetalleMovimiento.objects.create(
                    movimiento=movimiento,
                    presentacion_id=item['id'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'],
                    subtotal=subtotal
                )

                # Actualizar el stock del producto
                presentacion = get_object_or_404(Presentacion, id=item['id'])
                presentacion.stock -= item['cantidad']
                presentacion.total_neto = presentacion.valor * presentacion.stock
                presentacion.save()

                # Verificar si el stock ha llegado al mínimo
                if presentacion.stock <= presentacion.stock_minimo:
                    alertas_stock_minimo.append(
                        f"Has llegado al stock mínimo en {presentacion.producto.nombre} "
                        f"({presentacion.valor} {presentacion.categoria_unidad.unidad_medida.abreviatura}). "
                        f"Aviso: Realizar compra."
                    )

            del request.session['carrito']

            factura_url = reverse('generar_factura_pdf', args=[venta.id_venta])

            # Devolver las alertas de stock mínimo en la respuesta
            return JsonResponse({
                'success': True,
                'factura_url': factura_url,
                'alertas_stock_minimo': alertas_stock_minimo
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        
@login_required
#  CREAR CLIENTE (DENTRO DE LA VENTA)
def Crear_Clientes2(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()  
        return redirect('nueva_venta')  
    else:
        form = ClienteForm()

@login_required
def detalle_venta(request, id_venta):
    venta = get_object_or_404(Ventas, id_venta=id_venta)
    detalles = DetalleVentas.objects.filter(venta=venta)
    
    detalles_data = []
    for detalle in detalles:
        detalles_data.append({
            'presentacion': f"{detalle.presentacion.producto.nombre} - {detalle.presentacion.valor} {detalle.presentacion.categoria_unidad.unidad_medida.nombre}",
            'cantidad': detalle.cantidad,
            'precio_unitario': detalle.precio_unitario,
            'precio_unitario_bs': detalle.precio_unitario_bs,
            'subtotal': detalle.subtotal,
            'subtotal_bs': detalle.subtotal_bs,
        })
    
    data = {
        'id_venta': venta.id_venta,
        'numero_factura': venta.numero_factura,
        'cliente': venta.cliente.nombre,
        'fecha_venta': venta.fecha_venta.strftime('%d-%m-%Y'),
        'total': venta.total,
        'total_bs': venta.total_bs,
        'detalles': detalles_data,
    }
    
    return JsonResponse(data)

def generar_factura_pdf(request, id_venta):
    venta = Ventas.objects.get(id_venta=id_venta)
    detalles = DetalleVentas.objects.filter(venta=venta)
    tasa_cambio = TasaCambio.objects.filter(
                moneda_origen__codigo='USD',
                moneda_destino__codigo='VES'
            ).order_by('-fecha').first()

    if tasa_cambio:
        tasa = Decimal(str(tasa_cambio.tasa))
    else:
        tasa = Decimal(0)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{venta.numero_factura}.pdf"'

    # Ajustando el margen
    margen = 5 * mm  # margen de 10 mm

    # Nuevas dimensiones de la página (con margen)
    width = 200 * mm - 2 * margen  # Restar margen de ambos lados
    height = 300 * mm - 2 * margen  # Restar margen superior e inferior
    p = canvas.Canvas(response, pagesize=(width + 2 * margen, height + 2 * margen))  # Añadir márgenes al tamaño total
    p.setFont("Helvetica", 8)
    moneda_seleccionada = "USD"

    # Encabezado de la factura (con margen)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2 + margen, height - 10 * mm, "Deype Pinturas Aldana")
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2 + margen, height - 15 * mm, "RIF: J-0122537-1 | Teléfono: 0241-12138212")
    p.drawCentredString(width / 2 + margen, height - 20 * mm, "La Bocaina 1A, Avenida Bella Vista, Valencia, estado Carabobo")
    p.drawCentredString(width / 2 + margen, height - 25 * mm, "Valencia - Edo Carabobo")

    # Información de la tasa de cambio (con margen)
    p.setFont("Helvetica-Bold", 8)
    p.drawString(10 * mm + margen, height - 35 * mm, f"Tasa de Cambio: 1 {moneda_seleccionada} = {tasa} Bs")

    # Información de la factura (con margen)
    p.setFont("Helvetica", 8)
    p.drawString(10 * mm + margen, height - 45 * mm, f"N° Factura: {venta.numero_factura}")
    fecha_formateada = venta.fecha_venta.strftime("%d/%m/%Y %H:%M")
    p.drawString(10 * mm + margen, height - 50 * mm, f"Fecha: {fecha_formateada}")
    p.drawString(10 * mm + margen, height - 55 * mm, f"Nombre: {venta.cliente.nombre}")
    p.drawString(10 * mm + margen, height - 60 * mm, f"Cédula: {venta.cliente.cedula}")
    p.drawString(10 * mm + margen, height - 65 * mm, f"Dirección: {venta.cliente.direccion}")

    # Detalles de la factura (con margen y ajustando el espacio entre detalles)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(10 * mm + margen, height - 75 * mm, "Detalles de la Factura")
    p.setFont("Helvetica", 8)
    y = height - 85 * mm  # Posición inicial para los detalles

    # Encabezados de la tabla (con margen y ajuste de distancia)
    p.drawString(10 * mm + margen, y, "Producto")
    p.drawString(60 * mm + margen, y, "Cantidad")
    p.drawString(80 * mm + margen, y, f"Precio ({moneda_seleccionada})")
    p.drawString(105 * mm + margen, y, "Precio (Bs)")
    p.drawString(130 * mm + margen, y, f"Subtotal ({moneda_seleccionada})")
    p.drawString(160 * mm + margen, y, "Subtotal (Bs)")
    y -= 3 * mm  # Reducir espacio entre filas
    p.line(10 * mm + margen, y, width - 10 * mm + margen, y)  # Línea divisoria

    # Detalles de los productos (con margen y ajuste de distancia)
    for detalle in detalles:
        y -= 7 * mm  # Ajustando el espacio entre filas
        producto_info = f"{detalle.presentacion.producto.nombre} - {detalle.presentacion.valor} {detalle.presentacion.categoria_unidad.unidad_medida.abreviatura}"
        p.drawString(10 * mm + margen, y, producto_info)
        p.drawString(60 * mm + margen, y, str(detalle.cantidad))

        # Precios y subtotales
        precio_unitario = Decimal(str(detalle.precio_unitario))
        precio_bs = precio_unitario * tasa
        subtotal = Decimal(str(detalle.cantidad)) * precio_unitario
        subtotal_bs = subtotal * tasa

        p.drawString(80 * mm + margen, y, f"{precio_unitario:.2f} {moneda_seleccionada}")
        p.drawString(105 * mm + margen, y, f"Bs {precio_bs:.2f}")
        p.drawString(130 * mm + margen, y, f"{subtotal:.2f} {moneda_seleccionada}")
        p.drawString(160 * mm + margen, y, f"Bs {subtotal_bs:.2f}")

    # Línea divisora después de productos
    y -= 7 * mm
    p.line(10 * mm + margen, y, width - 10 * mm + margen, y)

    # Totales (moviéndolos a la derecha)
    total = Decimal(str(venta.total))
    total_bs = total * tasa

    p.setFont("Helvetica-Bold", 12)
    p.drawString(130 * mm + margen, y - 20 * mm, f"Subtotal ({moneda_seleccionada}): {total - venta.impuesto:.2f}")
    p.drawString(130 * mm + margen, y - 25 * mm, f"Impuesto ({moneda_seleccionada}): {venta.impuesto:.2f}")
    p.drawString(130 * mm + margen, y - 30 * mm, f"Total ({moneda_seleccionada}): {total:.2f}")
    p.drawString(130 * mm + margen, y - 35 * mm, f"Total (Bs): Bs {total_bs:.2f}")

    # Finalizar el PDF
    p.showPage()
    p.save()

    return response