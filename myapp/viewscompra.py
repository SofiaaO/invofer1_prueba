from django.db.models import Q, Max
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from myapp.forms import ProveedorForm
from .models import DetalleMovimiento, Moneda, Movimiento, Presentacion, Proveedor, Compras, DetalleCompras, TasaCambio
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from django.contrib.auth.decorators import login_required
from decimal import Decimal
@login_required
def listar_compras(request):
    query = request.GET.get('buscar', '')
    fecha = request.GET.get('fecha', '')

    compras = Compras.objects.all()

    if query:
        compras = compras.filter(
            Q(numero_factura__istartswith=query) | Q(proveedor__nombre__istartswith=query)
        )

    if fecha:
        compras = compras.filter(fecha_compra__date=fecha)

    return render(request, 'Compras/compras_list.html', {'compras': compras})

@login_required
def nueva_compra(request):
    if 'carrito_compras' not in request.session:
        request.session['carrito_compras'] = []  # Inicializar el carrito de compras

    carrito = request.session.get('carrito_compras', [])
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

    presentaciones = Presentacion.objects.filter(estado=True)
    proveedores = Proveedor.objects.all()

    last_factura = Compras.objects.aggregate(Max('numero_factura'))
    last_number = last_factura['numero_factura__max']
    numero_factura = str(int(last_number) + 1).zfill(6) if last_number else '000001'

    current_date = timezone.now().strftime('%d-%m-%Y')
    return render(request, 'Compras/compras.html', {
        'presentaciones': presentaciones,
        'carrito': carrito,
        'total': total,
        'proveedores': proveedores,
        'current_date': current_date,
        'numero_factura': numero_factura,
        'monedas': monedas,
        'moneda_seleccionada': moneda_seleccionada,
        'simbolo_moneda': simbolo_moneda,  # Pasar el símbolo de la moneda
        'tasa':tasa_cambio
    })
from django.contrib.auth.decorators import login_required
@login_required
def agregar_producto_compra(request):
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

        if "proveedor_id" in request.POST:
            request.session["proveedor_id"] = request.POST["proveedor_id"]

        presentacion = get_object_or_404(Presentacion, pk=id_presentacion)

        if 'carrito_compras' not in request.session:
            request.session['carrito_compras'] = []  # Inicializar si no existe

        carrito = request.session.get('carrito_compras', [])

        for item in carrito:
            if item['id'] == presentacion.id:
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

        request.session['carrito_compras'] = carrito
        return redirect('nueva_compra')
    
from django.http import JsonResponse

@login_required
def editar_cantidad(request):
    if request.method == "POST":
        id_presentacion = request.POST.get("id")
        nueva_cantidad = int(request.POST.get("cantidad", 1))  

        carrito = request.session.get('carrito_compras', [])  

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
                # Actualizar la cantidad y el subtotal
                item['cantidad'] = nueva_cantidad
                item['subtotal'] = item['cantidad'] * item['precio']
                item['subtotal_bs'] = item['subtotal'] * tasa  # Actualizar subtotal en Bs
                subtotal_actualizado = item['subtotal']  
                subtotal_bs_actualizado = item['subtotal_bs']  # Subtotal en Bs actualizado
                break

        request.session['carrito_compras'] = carrito

        total = sum(item['cantidad'] * item['precio'] for item in carrito)
        total_bs = total * tasa  # Total en Bs

        return JsonResponse({
            "success": True,
            "cantidad": nueva_cantidad,
            "subtotal": subtotal_actualizado,  
            "subtotal_bs": subtotal_bs_actualizado,  # Subtotal en Bs
            "total": total,
            "total_bs": total_bs  # Total en Bs
        })

    return JsonResponse({"success": False, "error": "Solicitud inválida"})


@login_required
def eliminar_producto_compra(request):
    if request.method == 'POST':
        id_producto = int(request.POST['id_producto'])
        carrito = request.session.get('carrito_compras', [])
        carrito = [item for item in carrito if item['id'] != id_producto]
        request.session['carrito_compras'] = carrito
        return redirect('nueva_compra')
    
    from django.contrib import messages


@login_required
def guardar_compra(request):
    if request.method == 'POST':
        try:
            proveedor_id = request.POST['proveedor_id']
            proveedor = get_object_or_404(Proveedor, rif=proveedor_id)

            moneda_seleccionada = request.session.get('moneda_seleccionada', 'USD')
            tasa_cambio = TasaCambio.objects.filter(
                moneda_origen__codigo=moneda_seleccionada,
                moneda_destino__codigo='VES'
            ).order_by('-fecha').first()

            if tasa_cambio:
                tasa = float(tasa_cambio.tasa)
            else:
                tasa = 0 
            last_factura = Compras.objects.aggregate(Max('numero_factura'))
            last_number = last_factura['numero_factura__max']
            numero_factura = str(int(last_number) + 1).zfill(6) if last_number else '000001'

            if 'carrito_compras' not in request.session:
                return JsonResponse({
                    'success': False,
                    'error': 'El carrito de compras está vacío.'
                })

            carrito = request.session.get('carrito_compras', [])
            total = sum(item['cantidad'] * item['precio'] for item in carrito)
            total_bs = total * tasa 

            compra = Compras.objects.create(
                numero_factura=numero_factura,
                proveedor=proveedor,
                total=total,
                total_bs=total_bs 
            )

            movimiento = Movimiento.objects.create(
                tipo_movimiento='compra',
                fecha_movimiento=timezone.now(),
                usuario=request.user,
                proveedor=proveedor,
                total=total,
                descripcion=f"Compra realizada N° {numero_factura}"
            )

            for item in carrito:
                subtotal = item['cantidad'] * item['precio']
                subtotal_bs = subtotal * tasa 
                DetalleCompras.objects.create(
                    compra=compra,
                    presentacion_id=item['id'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'],
                    precio_unitario_bs=item['precio'] * tasa,  # Guardar el precio unitario en Bs
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

                presentacion = get_object_or_404(Presentacion, id=item['id'])
                presentacion.stock += item['cantidad']
                presentacion.total_neto = presentacion.valor * presentacion.stock
                presentacion.save()

            del request.session['carrito_compras']
            messages.success(request, 'Compra registrada correctamente.')
            compra_url = reverse('generar_comprobante_compra_pdf', args=[compra.id_compra])
            return JsonResponse({
                'success': True,
                'compra_url': compra_url
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@login_required
def detalle_compra(request, id_compra):
    compra = get_object_or_404(Compras, id_compra=id_compra)
    detalles = DetalleCompras.objects.filter(compra=compra)
    
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
        'id_compra': compra.id_compra,
        'numero_factura': compra.numero_factura,
        'proveedor': compra.proveedor.nombre,
        'fecha_compra': compra.fecha_compra.strftime('%d-%m-%Y'),
        'total': compra.total,
        'total_bs': compra.total_bs,
        'detalles': detalles_data,
    }
    
    return JsonResponse(data)


@login_required
def Crear_Proveedores2(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()  
        return redirect('nueva_compra')  
    else:
        form = ProveedorForm()

@login_required
def generar_comprobante_compra_pdf(request, id_compra):
    compra = Compras.objects.get(id_compra=id_compra)
    detalles = DetalleCompras.objects.filter(compra=compra)

    # Obtener la tasa de cambio actual
    tasa_cambio = TasaCambio.objects.filter(
                moneda_origen__codigo='USD',
                moneda_destino__codigo='VES'
            ).order_by('-fecha').first()

    if tasa_cambio:
        tasa = Decimal(str(tasa_cambio.tasa))
    else:
        tasa = Decimal(0)

    # Configurar la respuesta en PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="comprobante_compra_{compra.numero_factura}.pdf"'

    # Ajustar el margen y las dimensiones de la página
    margen = 5 * mm
    width = 200 * mm - 2 * margen
    height = 300 * mm - 2 * margen
    p = canvas.Canvas(response, pagesize=(width + 2 * margen, height + 2 * margen))
    p.setFont("Helvetica", 8)

    # Encabezado del comprobante
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2 + margen, height - 10 * mm, "COMPROBANTE DE COMPRA")
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2 + margen, height - 15 * mm, "Deype Pinturas Aldana")
    p.drawCentredString(width / 2 + margen, height - 20 * mm, "RIF: J-0122537-1 | Teléfono: 0241-12138212")
    p.drawCentredString(width / 2 + margen, height - 25 * mm, "La Bocaina 1A, Avenida Bella Vista, Valencia, estado Carabobo")
    p.drawCentredString(width / 2 + margen, height - 30 * mm, "Valencia - Edo Carabobo")

    # Información de la tasa de cambio
    p.setFont("Helvetica-Bold", 8)
    p.drawString(10 * mm + margen, height - 40 * mm, f"Tasa de Cambio: 1 USD = {tasa} Bs")

    # Información del comprobante
    p.setFont("Helvetica", 8)
    p.drawString(10 * mm + margen, height - 50 * mm, f"N° Compra: {compra.numero_factura}")
    fecha_formateada = compra.fecha_compra.strftime("%d/%m/%Y %H:%M")
    p.drawString(10 * mm + margen, height - 55 * mm, f"Fecha: {fecha_formateada}")
    p.drawString(10 * mm + margen, height - 60 * mm, f"Proveedor: {compra.proveedor.nombre}")
    p.drawString(10 * mm + margen, height - 65 * mm, f"RIF: {compra.proveedor.rif}")
    p.drawString(10 * mm + margen, height - 70 * mm, f"Dirección: {compra.proveedor.direccion}")

    # Detalles de la compra
    p.setFont("Helvetica-Bold", 10)
    p.drawString(10 * mm + margen, height - 80 * mm, "Detalles de la Compra")
    p.setFont("Helvetica", 8)

    y = height - 90 * mm
    p.drawString(10 * mm + margen, y, "Producto")
    p.drawString(60 * mm + margen, y, "Cantidad")
    p.drawString(80 * mm + margen, y, "Precio (USD)")
    p.drawString(105 * mm + margen, y, "Precio (Bs)")
    p.drawString(130 * mm + margen, y, "Subtotal (USD)")
    p.drawString(160 * mm + margen, y, "Subtotal (Bs)")
    y -= 3 * mm
    p.line(10 * mm + margen, y, width - 10 * mm + margen, y)

    # Detalles de los productos
    for detalle in detalles:
        y -= 7 * mm
        producto_info = f"{detalle.presentacion.producto.nombre} - {detalle.presentacion.valor} {detalle.presentacion.categoria_unidad.unidad_medida.abreviatura}"
        p.drawString(10 * mm + margen, y, producto_info)
        p.drawString(60 * mm + margen, y, str(detalle.cantidad))

        # Precios y subtotales
        precio_unitario = Decimal(str(detalle.precio_unitario))
        precio_bs = precio_unitario * tasa
        subtotal = Decimal(str(detalle.cantidad)) * precio_unitario
        subtotal_bs = subtotal * tasa

        p.drawString(80 * mm + margen, y, f"${precio_unitario:.2f}")
        p.drawString(105 * mm + margen, y, f"Bs {precio_bs:.2f}")
        p.drawString(130 * mm + margen, y, f"${subtotal:.2f}")
        p.drawString(160 * mm + margen, y, f"Bs {subtotal_bs:.2f}")

    # Línea divisoria después de productos
    y -= 7 * mm
    p.line(10 * mm + margen, y, width - 10 * mm + margen, y)

    # Totales
    total = Decimal(str(compra.total))
    total_bs = total * tasa

    p.setFont("Helvetica-Bold", 12)
    p.drawString(130 * mm + margen, y - 20 * mm, f"Total (USD): ${total:.2f}")
    p.drawString(130 * mm + margen, y - 25 * mm, f"Total (Bs): Bs {total_bs:.2f}")

    # Finalizar el PDF
    p.showPage()
    p.save()

    return response
