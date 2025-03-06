from django.db.models import Q, Max
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from myapp.forms import ProveedorForm
from .models import DetalleMovimiento, Movimiento, Presentacion, Proveedor, Compras, DetalleCompras
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

def listar_compras(request):
    query = request.GET.get('buscar', '')
    fecha = request.GET.get('fecha', '')

    compras = Compras.objects.all().order_by('-fecha_compra')

    if query:
        compras = compras.filter(
            Q(numero_factura__istartswith=query) | Q(proveedor__nombre__istartswith=query)
        )

    if fecha:
        compras = compras.filter(fecha_compra__date=fecha)

    return render(request, 'Compras/compras_list.html', {'compras': compras})

def nueva_compra(request):
    if 'carrito_compras' not in request.session:
        request.session['carrito_compras'] = []  # Inicializar el carrito de compras

    carrito = request.session.get('carrito_compras', [])
    total = sum(item['cantidad'] * item['precio'] for item in carrito)

    presentaciones = Presentacion.objects.all()
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
    })

def agregar_producto_compra(request):
    if request.method == 'POST':
        id_presentacion = request.POST['id_presentacion']
        cantidad = int(request.POST['cantidad'])

        if "proveedor_id" in request.POST:
            request.session["proveedor_id"] = request.POST["proveedor_id"]

        presentacion = get_object_or_404(Presentacion, pk=id_presentacion)

        if 'carrito_compras' not in request.session:
            request.session['carrito_compras'] = []  # Inicializar si no existe

        carrito = request.session.get('carrito_compras', [])

        for item in carrito:
            if item['id'] == presentacion.id:
                item['cantidad'] += cantidad
                item['subtotal'] = item['cantidad'] * float(presentacion.precio_compra)
                break
        else:
            carrito.append({
                'id': presentacion.id,
                'codigo': presentacion.codigo,
                'nombre': f"{presentacion.producto.nombre} - {presentacion.valor} {presentacion.categoria_unidad.unidad_medida.nombre}",
                'cantidad': cantidad,
                'precio': float(presentacion.precio_compra),
                'subtotal': cantidad * float(presentacion.precio_compra),
            })

        request.session['carrito_compras'] = carrito
        return redirect('nueva_compra')
    
from django.http import JsonResponse

def editar_cantidad(request):
    if request.method == "POST":
        id_presentacion = request.POST.get("id")
        nueva_cantidad = int(request.POST.get("cantidad", 1))  

        carrito = request.session.get('carrito_compras', [])  

        for item in carrito:
            if item['id'] == int(id_presentacion):
                item['cantidad'] = nueva_cantidad
                item['subtotal'] = item['cantidad'] * item['precio']
                subtotal_actualizado = item['subtotal']  
                break

        request.session['carrito_compras'] = carrito  

        total = sum(item['cantidad'] * item['precio'] for item in carrito)

        return JsonResponse({
            "success": True,
            "cantidad": nueva_cantidad,
            "subtotal": subtotal_actualizado,  
            "total": total  
        })

    return JsonResponse({"success": False, "error": "Solicitud inválida"})

    
def eliminar_producto_compra(request):
    if request.method == 'POST':
        id_producto = int(request.POST['id_producto'])
        carrito = request.session.get('carrito_compras', [])
        carrito = [item for item in carrito if item['id'] != id_producto]
        request.session['carrito_compras'] = carrito
        return redirect('nueva_compra')
    
    from django.contrib import messages

def guardar_compra(request):
    if request.method == 'POST':
        try:
            proveedor_id = request.POST['proveedor_id']
            proveedor = get_object_or_404(Proveedor, rif=proveedor_id)

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

            compra = Compras.objects.create(
                numero_factura=numero_factura,
                proveedor=proveedor,
                total=total
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
                DetalleCompras.objects.create(
                    compra=compra,
                    presentacion_id=item['id'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'],
                    subtotal=subtotal
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
    
def detalle_compra(request, id_compra):
    compra = get_object_or_404(Compras, id_compra=id_compra)
    detalles = DetalleCompras.objects.filter(compra=compra)
    
    detalles_data = []
    for detalle in detalles:
        detalles_data.append({
            'presentacion': f"{detalle.presentacion.producto.nombre} - {detalle.presentacion.valor} {detalle.presentacion.categoria_unidad.unidad_medida.nombre}",
            'cantidad': detalle.cantidad,
            'precio_unitario': detalle.precio_unitario,
            'subtotal': detalle.subtotal,
        })
    
    data = {
        'id_compra': compra.id_compra,
        'numero_factura': compra.numero_factura,
        'proveedor': compra.proveedor.nombre,
        'fecha_compra': compra.fecha_compra.strftime('%d-%m-%Y'),
        'total': compra.total,
        'detalles': detalles_data,
    }
    
    return JsonResponse(data)

def Crear_Proveedores2(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()  
        return redirect('nueva_compra')  
    else:
        form = ProveedorForm()

def generar_comprobante_compra_pdf(request, id_compra):
    compra = Compras.objects.get(id_compra=id_compra)
    detalles = DetalleCompras.objects.filter(compra=compra)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="comprobante_compra_{compra.numero_factura}.pdf"'


    width = 100 * mm
    height = 200 * mm
    p = canvas.Canvas(response, pagesize=(width, height))
    p.setFont("Helvetica", 8)


    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2, height - 10 * mm, "COMPROBANTE DE COMPRA")
    p.setFont("Helvetica", 8)


    p.drawString(10 * mm, height - 20 * mm, f"Proveedor: {compra.proveedor.nombre}")
    p.drawString(10 * mm, height - 25 * mm, f"RIF: {compra.proveedor.rif}")
    p.drawString(10 * mm, height - 30 * mm, f"Dirección: {compra.proveedor.direccion}")
    p.drawString(10 * mm, height - 35 * mm, f"Teléfono: {compra.proveedor.telefono}")

    p.line(10 * mm, height - 40 * mm, width - 10 * mm, height - 40 * mm)

    p.drawString(10 * mm, height - 45 * mm, f"N° Compra: {compra.numero_factura}")
    fecha_formateada = compra.fecha_compra.strftime("%d/%m/%Y %H:%M")
    p.drawString(10 * mm, height - 50 * mm, f"Fecha: {fecha_formateada}")

    p.setFont("Helvetica-Bold", 10)
    p.drawString(10 * mm, height - 60 * mm, "Detalles de la Compra")
    p.setFont("Helvetica", 8)

    y = height - 65 * mm
    p.drawString(10 * mm, y, "Producto")
    p.drawString(45 * mm, y, "Cantidad")
    p.drawString(65 * mm, y, "Precio")
    p.drawString(80 * mm, y, "Subtotal")
    y -= 5 * mm
    p.line(10 * mm, y, width - 10 * mm, y)

    for detalle in detalles:
        y -= 5 * mm
        producto_info = f"{detalle.presentacion.producto.nombre} - {detalle.presentacion.valor} {detalle.presentacion.categoria_unidad.unidad_medida.nombre}"
        p.drawString(10 * mm, y, producto_info)
        p.drawString(50 * mm, y, str(detalle.cantidad))
        p.drawString(65 * mm, y, f"${detalle.precio_unitario}")
        p.drawString(80 * mm, y, f"${detalle.cantidad * detalle.precio_unitario}")

    y -= 10 * mm
    p.line(10 * mm, y, width - 10 * mm, y)
    p.drawRightString(width - 10 * mm, y - 5 * mm, f"Subtotal: ${compra.total}")
    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(width - 10 * mm, y - 10 * mm, f"Total: ${compra.total}")

    p.showPage()
    p.save()

    return response