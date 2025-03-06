import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Max
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
import json
from myapp.forms import ClienteForm
from .models import DetalleMovimiento, Movimiento, Ventas, DetalleVentas, Presentacion, Cliente
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

def listar_ventas(request):
    query = request.GET.get('buscar', '')
    fecha = request.GET.get('fecha', '')

    ventas = Ventas.objects.all().order_by('-fecha_venta')

    if query:
        ventas = ventas.filter(
            Q(numero_factura__istartswith=query) | Q(cliente__nombre__istartswith=query)
        )

    if fecha:
        ventas = ventas.filter(fecha_venta__date=fecha)

    return render(request, 'ventas/ventas_list.html', {'ventas': ventas})

# REGISTRAR NUEVA VENTA
def nueva_venta(request):

    if 'carrito' not in request.session:
        request.session['carrito'] = []

    carrito = request.session['carrito']
    total = sum(item['cantidad'] * item['precio'] for item in carrito)


    presentaciones = Presentacion.objects.all()
    clientes = Cliente.objects.all()


    last_factura = Ventas.objects.aggregate(Max('numero_factura'))
    last_number = last_factura['numero_factura__max']
    numero_factura = str(int(last_number) + 1).zfill(6) if last_number else '000001'

    current_date = timezone.now().strftime('%d-%m-%Y') 

    return render(request, 'ventas/ventas.html', {
        'presentaciones': presentaciones,
        'carrito': carrito,
        'total': total,
        'clientes': clientes,
        'current_date': current_date,
        'numero_factura': numero_factura,
    })
# EDITAR CANTIDAD EN EL CARRITO
def editar_cantidad_ventas(request):
    if request.method == "POST":
        id_presentacion = request.POST.get("id")
        nueva_cantidad = int(request.POST.get("cantidad", 1))  
        carrito = request.session.get('carrito', [])

        for item in carrito:
            if item['id'] == int(id_presentacion):
                item['cantidad'] = nueva_cantidad
                item['subtotal'] = item['cantidad'] * item['precio']
                subtotal_actualizado = item['subtotal']  
                break

        request.session['carrito'] = carrito


        total = sum(item['cantidad'] * item['precio'] for item in carrito)

        return JsonResponse({
            "success": True,
            "cantidad": nueva_cantidad,
            "subtotal": subtotal_actualizado,  
            "total": total 
        })

    return JsonResponse({"success": False, "error": "Solicitud inválida"})

# AGREGAR PRESENTACIÓN AL CARRITO
def agregar_producto(request):
    if request.method == 'POST':
        id_presentacion = request.POST['id_presentacion']
        cantidad = int(request.POST['cantidad'])

        if "cliente_id" in request.POST:
            request.session["cliente_id"] = request.POST["cliente_id"]

        
        presentacion = get_object_or_404(Presentacion, pk=id_presentacion)

        carrito = request.session.get('carrito', [])

        for item in carrito:
            if item['id'] == presentacion.id:
                item['cantidad'] += cantidad
                item['subtotal'] = item['cantidad'] * float(presentacion.precio_venta)
                break
        else:
            carrito.append({
                'id': presentacion.id,
                'codigo': presentacion.codigo,
                'nombre': f"{presentacion.producto.nombre} - {presentacion.valor} {presentacion.categoria_unidad.unidad_medida.nombre}",
                'cantidad': cantidad,
                'precio': float(presentacion.precio_venta),
                'subtotal': cantidad * float(presentacion.precio_venta),
            })

        request.session['carrito'] = carrito

        return redirect('nueva_venta')


# ELIMINAR PRODUCTO DEL CARRITO
def eliminar_producto(request):
    if request.method == 'POST':
        id_producto = int(request.POST['id_producto'])
        carrito = request.session.get('carrito', [])
        carrito = [item for item in carrito if item['id'] != id_producto]
        request.session['carrito'] = carrito

        return redirect('nueva_venta')

# GUARDAR VENTA

from django.http import JsonResponse
from django.urls import reverse

def guardar_venta(request):
    if request.method == 'POST':
        try:
            cliente_id = request.POST['cliente_id']
            cliente = get_object_or_404(Cliente, cedula=cliente_id)

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

            venta = Ventas.objects.create(
                numero_factura=numero_factura,
                cliente=cliente,
                total=total
            )

            movimiento = Movimiento.objects.create(
                tipo_movimiento='venta',
                fecha_movimiento=timezone.now(),
                usuario=request.user,
                cliente=cliente,
                total=total,
                descripcion=f"Venta realizada con factura {numero_factura}"
            )

            for item in carrito:
                subtotal = item['cantidad'] * item['precio']
    
                DetalleVentas.objects.create(
                    venta=venta,
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

                # Actualizar el stock del producto
                presentacion = get_object_or_404(Presentacion, id=item['id'])
                presentacion.stock -= item['cantidad']
                presentacion.total_neto = presentacion.valor * presentacion.stock
                presentacion.save()

            del request.session['carrito']

            factura_url = reverse('generar_factura_pdf', args=[venta.id_venta])

            return JsonResponse({
                'success': True,
                'factura_url': factura_url
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

        
#  CREAR CLIENTE (DENTRO DE LA VENTA)
def Crear_Clientes2(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()  
        return redirect('nueva_venta')  
    else:
        form = ClienteForm()

def detalle_venta(request, id_venta):
    venta = get_object_or_404(Ventas, id_venta=id_venta)
    detalles = DetalleVentas.objects.filter(venta=venta)
    
    detalles_data = []
    for detalle in detalles:
        detalles_data.append({
            'presentacion': f"{detalle.presentacion.producto.nombre} - {detalle.presentacion.valor} {detalle.presentacion.categoria_unidad.unidad_medida.nombre}",
            'cantidad': detalle.cantidad,
            'precio_unitario': detalle.precio_unitario,
            'subtotal': detalle.subtotal,
        })
    
    data = {
        'id_venta': venta.id_venta,
        'numero_factura': venta.numero_factura,
        'cliente': venta.cliente.nombre,
        'fecha_venta': venta.fecha_venta.strftime('%d-%m-%Y'),
        'total': venta.total,
        'detalles': detalles_data,
    }
    
    return JsonResponse(data)

def generar_factura_pdf(request, id_venta):
    venta = Ventas.objects.get(id_venta=id_venta)
    detalles = DetalleVentas.objects.filter(venta=venta)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{venta.numero_factura}.pdf"'

    width = 100 * mm  
    height = 200 * mm  
    p = canvas.Canvas(response, pagesize=(width, height))
    p.setFont("Helvetica", 8)  

    p.setFont("Helvetica-Bold", 12) 
    p.drawCentredString(width / 2, height - 10 * mm, "Deype Pinturas Aldana")
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2, height - 15 * mm, "RIF: J-0122537-1 | Teléfono: 0241-12138212")
    p.drawCentredString(width / 2, height - 20 * mm, "La Bocaina 1A, Avenida Bella Vista, Valencia, estado Carabobo")
    p.drawCentredString(width / 2, height - 25 * mm, "Valencia - Edo Carabobo")


    p.setFont("Helvetica-Bold", 10)  
    p.drawString(10 * mm, height - 40 * mm, f"N° Factura: {venta.numero_factura}")
    
    p.setFont("Helvetica", 8)  
    fecha_formateada = venta.fecha_venta.strftime("%d/%m/%Y %H:%M")  
    p.drawString(10 * mm, height - 45 * mm, f"Fecha: {fecha_formateada}")
    p.drawString(10 * mm, height - 50 * mm, f"Nombre: {venta.cliente.nombre}")
    p.drawString(10 * mm, height - 55 * mm, f"Cédula: {venta.cliente.cedula}")
    p.drawString(10 * mm, height - 60 * mm, f"Dirección: {venta.cliente.direccion}")


    p.setFont("Helvetica-Bold", 10)  
    p.drawString(10 * mm, height - 70 * mm, "Detalles de la Factura")
    p.setFont("Helvetica", 8)  
    y = height - 80 * mm
    p.drawString(10 * mm, y, "Producto")
    p.drawString(50 * mm, y, "Cantidad")
    p.drawString(65 * mm, y, "Precio")
    p.drawString(80 * mm, y, "Subtotal")
    y -= 5 * mm
    p.line(10 * mm, y, width - 10 * mm, y)

    for detalle in detalles:
        y -= 5 * mm
        producto_info = f"{detalle.presentacion.producto.nombre} - {detalle.presentacion.valor} {detalle.presentacion.categoria_unidad.unidad_medida.nombre}"
        p.drawString(10 * mm, y, producto_info)
        p.drawString(52 * mm, y, str(detalle.cantidad))  
        p.drawString(65 * mm, y, f"${detalle.precio_unitario}")
        p.drawString(80 * mm, y, f"${detalle.cantidad * detalle.precio_unitario}")

    y -= 10 * mm
    p.line(10 * mm, y, width - 10 * mm, y)
    p.drawRightString(width - 10 * mm, y - 5 * mm, f"Subtotal: ${venta.total}")
    p.drawRightString(width - 10 * mm, y - 10 * mm, f"IVA (16%): $")
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width - 10 * mm, y - 15 * mm, f"Total: ${venta.total}")


    p.setFont("Helvetica", 8)  

    p.showPage()
    p.save()

    return response