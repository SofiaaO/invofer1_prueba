from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Categoria, Marca, Producto, Presentacion, CategoriaUnidadMedida,UnidadMedida
from .forms import ProductoForm, PresentacionForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Categoria, Marca


@login_required
def listar_productos(request):
    buscar = request.GET.get('buscar', '') 
    categoria_id = request.GET.get('categoria', '')  

    productos = Producto.objects.all().order_by('id')
    if buscar:
        productos = productos.filter(
            Q(nombre__nombre__icontains=buscar) | Q(id__icontains=buscar)
        )

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    categorias = Categoria.objects.all()  
    marcas = Marca.objects.all()  

    paginator = Paginator(productos, 10)  
    page_number = request.GET.get('page')
    productos_paginados = paginator.get_page(page_number)

    return render(request, 'Productos/productos_list.html', {
        'productos': productos_paginados,
        'categorias': categorias,
        'marcas': marcas,
        'buscar': buscar,
        'categoria_id': categoria_id,
    })

@login_required
def crear_producto(request):
    categorias = Categoria.objects.all() 
    marcas = Marca.objects.all()  

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        categoria_id = request.POST.get('categoria')
        marca_id = request.POST.get('marca')
        estado = request.POST.get('estado') == 'on'  # Convertir a booleano

        # Validar los datos
        if not nombre or not categoria_id or not marca_id:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('crear_producto')

        try:
            categoria = Categoria.objects.get(id=categoria_id)
            marca = Marca.objects.get(id=marca_id)
        except (Categoria.DoesNotExist, Marca.DoesNotExist):
            messages.error(request, "Categoría o marca no válida.")
            return redirect('crear_producto')

        # Crear el producto
        producto = Producto(
            nombre=nombre,
            categoria=categoria,
            marca=marca,
            estado=estado
        )
        producto.save()

        messages.success(request, "Producto creado con éxito.")
        return redirect('lista_productos')

    return render(request, 'Productos/crear_producto.html', {
        'categorias': categorias,
        'marcas': marcas,
    })

@login_required
def editar_producto(request, id):
    print(f"Método recibido: {request.method}")  # Depuración

    producto = get_object_or_404(Producto, id=id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('lista_productos')

    return redirect('lista_productos')


@login_required
def crear_presentacion(request):
    productos = Producto.objects.all()
    unidades = CategoriaUnidadMedida.objects.all()
    categorias = Categoria.objects.all()  # Obtener todas las categorías

    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        codigo = request.POST.get('codigo')
        categoria_unidad_id = request.POST.get('categoria_unidad')
        valor = request.POST.get('valor')
        precio_venta = request.POST.get('precio_venta')
        precio_compra = request.POST.get('precio_compra')
        stock = request.POST.get('stock')
        stock_minimo = request.POST.get('stock_minimo')
        estado = request.POST.get('estado') == 'on'

        if not producto_id or not codigo or not categoria_unidad_id or not valor or not precio_venta or not precio_compra or not stock or not stock_minimo:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('crear_presentacion')

        try:
            producto = Producto.objects.get(id=producto_id)
            categoria_unidad = CategoriaUnidadMedida.objects.get(id=categoria_unidad_id)
        except (Producto.DoesNotExist, CategoriaUnidadMedida.DoesNotExist):
            messages.error(request, "Producto o unidad de medida no válida.")
            return redirect('crear_presentacion')

        if Presentacion.objects.filter(codigo=codigo).exists():
            messages.error(request, "El código ya está en uso. Por favor, genera un nuevo código.")
            return redirect('crear_presentacion')

        presentacion = Presentacion(
            producto=producto,
            codigo=codigo,
            categoria_unidad=categoria_unidad,
            valor=valor,
            precio_venta=precio_venta,
            precio_compra=precio_compra,
            stock=stock,
            stock_minimo=stock_minimo,
            estado=estado,
            total_neto=float(valor) * int(stock)
        )
        presentacion.save()

        messages.success(request, "Presentación creada con éxito.")
        return redirect('lista_productos')

    return render(request, 'Productos/crear_presentacion.html', {
        'productos': productos,
        'unidades': unidades,
        'categorias': categorias,  # Pasar las categorías al contexto
    })

@login_required
def generar_codigo(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    prefijo = producto.nombre[:3].upper()

    ultima_presentacion = Presentacion.objects.filter(producto=producto).order_by('-id').first()
    if ultima_presentacion:
        ultimo_codigo = ultima_presentacion.codigo
        try:
            ultimo_numero = int(ultimo_codigo.split('-')[1])
            nuevo_numero = ultimo_numero + 1
        except (IndexError, ValueError):
            nuevo_numero = 1
    else:
        nuevo_numero = 1

    while True:
        nuevo_codigo = f"{prefijo}-{nuevo_numero}"
        if not Presentacion.objects.filter(codigo=nuevo_codigo).exists():
            break
        nuevo_numero += 1

    return JsonResponse({'codigo': nuevo_codigo})

@login_required
def listar_presentaciones(request):
    presentaciones = Presentacion.objects.all()
    return render(request, 'Productos/productos_list.html', {
        'presentaciones': presentaciones,
    })

@login_required
def editar_presentacion(request, id):
    presentacion = get_object_or_404(Presentacion, id=id)
    productos = Producto.objects.all()
    unidades = CategoriaUnidadMedida.objects.all()  

    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        codigo = request.POST.get('codigo')
        categoria_unidad_id = request.POST.get('categoria_unidad')
        valor = request.POST.get('valor')
        precio_venta = request.POST.get('precio_venta')
        precio_compra = request.POST.get('precio_compra')
        stock = request.POST.get('stock')
        stock_minimo = request.POST.get('stock_minimo')
        estado = request.POST.get('estado') == 'on'

        if not producto_id or not codigo or not categoria_unidad_id or not valor or not precio_venta or not precio_compra or not stock or not stock_minimo:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('editar_presentacion', id=id)

        try:
            producto = Producto.objects.get(id=producto_id)
            categoria_unidad = CategoriaUnidadMedida.objects.get(id=categoria_unidad_id)
        except (Producto.DoesNotExist, CategoriaUnidadMedida.DoesNotExist):
            messages.error(request, "Producto o unidad de medida no válida.")
            return redirect('editar_presentacion', id=id)


        # Actualizar la presentación
        presentacion.producto = producto
        presentacion.codigo = codigo
        presentacion.categoria_unidad = categoria_unidad
        presentacion.valor = valor
        presentacion.precio_venta = precio_venta
        presentacion.precio_compra = precio_compra
        presentacion.stock = stock
        presentacion.stock_minimo = stock_minimo
        presentacion.estado = estado
        presentacion.total_neto = float(valor) * int(stock)
        presentacion.save()

        messages.success(request, "Presentación actualizada con éxito.")
        return redirect('lista_productos')

    return render(request, 'Productos/crear_presentacion.html', {
        'presentacion': presentacion,
        'productos': productos,
        'unidades': unidades,
        'editar': True, 
    })
@login_required
def obtener_presentaciones(request, producto_id):
    presentaciones = Presentacion.objects.filter(producto_id=producto_id).values(
        'codigo',
        'categoria_unidad__unidad_medida__nombre',
        'valor',
        'precio_venta',
        'precio_compra',
        'stock',
        'stock_minimo',
        'estado',
        'total_neto'
    )
    return JsonResponse(list(presentaciones), safe=False)

@login_required
def obtener_unidades_por_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    categoria = producto.categoria  
    unidades = CategoriaUnidadMedida.objects.filter(categoria=categoria).values(
        'id', 'unidad_medida__nombre'
    )
    return JsonResponse({'unidades': list(unidades)})

@csrf_exempt
def crear_categoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            categoria = Categoria.objects.create(nombre=nombre)
            return JsonResponse({'success': True, 'id': categoria.id, 'nombre': categoria.nombre})
        return JsonResponse({'success': False, 'error': 'Nombre no proporcionado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@csrf_exempt
def crear_marca(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        if nombre:
            marca = Marca.objects.create(nombre=nombre)
            return JsonResponse({'success': True, 'id': marca.id, 'nombre': marca.nombre})
        return JsonResponse({'success': False, 'error': 'Nombre no proporcionado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

