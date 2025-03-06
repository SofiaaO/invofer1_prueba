from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Categoria, Marca, Producto_Marca_Categoria, Presentacion, CategoriaUnidadMedida
from .forms import ProductoMarcaCategoriaForm, PresentacionForm
from django.contrib import messages

def listar_productos(request):
    buscar = request.GET.get('buscar', '') 
    categoria_id = request.GET.get('categoria', '')  

    productos = Producto_Marca_Categoria.objects.all().order_by('id')
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
        'productos_marca_categoria': productos_paginados,
        'categorias': categorias,
        'marcas': marcas,
        'buscar': buscar,
        'categoria_id': categoria_id,
    })

def crear_producto(request):
    if request.method == 'POST':
        form = ProductoMarcaCategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado con éxito.")
            return redirect('lista_productos')  
    else:
        form = ProductoMarcaCategoriaForm()

    return render(request, 'Productos/crear_producto.html', {'form': form})
def editar_producto(request, id):
    producto = get_object_or_404(Producto_Marca_Categoria, id=id)

    if request.method == 'POST':
        form = ProductoMarcaCategoriaForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado con éxito.")
            return JsonResponse({'success': True})  # Respuesta JSON si el formulario es válido
        else:
            # Si el formulario no es válido, devolver errores
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

def crear_presentacion(request):
    if request.method == 'POST':
        form_presentacion = PresentacionForm(request.POST)
        if form_presentacion.is_valid():
            presentacion = form_presentacion.save(commit=False)

            if not presentacion.producto:
                return render(request, 'error.html', {'error': 'Debes seleccionar un producto.'})
            
            presentacion.total_neto = presentacion.valor * presentacion.stock
            presentacion.save()
            return redirect('lista_productos')  
    else:
        form_presentacion = PresentacionForm()

    return render(request, 'Productos/productos_agregar.html', {
        'form_presentacion': form_presentacion,
    })

def listar_presentaciones(request):
    presentaciones = Presentacion.objects.all()
    return render(request, 'Productos/productos_list.html', {
        'presentaciones': presentaciones,
    })

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

def obtener_unidades_por_producto(request, producto_id):
    producto = get_object_or_404(Producto_Marca_Categoria, id=producto_id)
    categoria = producto.categoria  
    unidades = CategoriaUnidadMedida.objects.filter(categoria=categoria).values(
        'id', 'unidad_medida__nombre'
    )
    return JsonResponse({'unidades': list(unidades)})