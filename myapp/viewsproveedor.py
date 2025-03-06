from django.contrib import messages
from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from myapp.models import *
from myapp.forms import *
# Create your views here.
from django.db.models import Q
from django.core.paginator import Paginator

def listar_proveedores(request):
    query = request.GET.get('buscar', '')

    if query:
        proveedores_list = Proveedor.objects.filter(
            Q(rif__istartswith=query) | Q(nombre__istartswith=query)
        )
    else:
        proveedores_list = Proveedor.objects.exclude(rif__isnull=True).exclude(rif="")

    paginator = Paginator(proveedores_list, 10)  
    page_number = request.GET.get('page')
    proveedores = paginator.get_page(page_number)

    return render(request, 'proveedores/proveedores_list.html', {'proveedores': proveedores})

def Crear_Proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()  
            messages.success(request, "Proveedor actualizado con éxito.")
            return redirect('Proveedor Listar')  
    else:
        messages.error(request, "Corrige los errores en el formulario.")
        form = ProveedorForm()

def editar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, id=id)  

    if request.method == 'POST':
        proveedor.rif = request.POST['rif']
        proveedor.nombre = request.POST['nombre']
        proveedor.telefono = request.POST['telefono']
        proveedor.direccion= request.POST['direccion']
        proveedor.direccion_fiscal= request.POST['direccion_fiscal']
        proveedor.productos_ofrecidos= request.POST['productos_ofrecidos']
        proveedor.estado = request.POST.get('estado', False) == 'on'
        proveedor.save()
        messages.success(request, "Proveedor actualizado con éxito.")
        return redirect('Proveedor Listar')  
 
    return render(request, 'editar_proveedor.html', {'proveedor': proveedor})
