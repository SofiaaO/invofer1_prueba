from django.contrib import messages
from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from myapp.models import *
from myapp.forms import *
# Create your views here.
from django.db.models import Q
from django.core.paginator import Paginator

def listar_clientes(request):
    query = request.GET.get('buscar', '')
    clientes_list = Cliente.objects.all()

    if query:
        clientes_list = clientes_list.filter(
            Q(cedula__istartswith=query) | Q(nombre__istartswith=query)
        )

    paginator = Paginator(clientes_list, 10) 
    page_number = request.GET.get('page')
    clientes = paginator.get_page(page_number)

    return render(request, 'clientes/clientes_list.html', {'clientes': clientes})

def Crear_Clientes2(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()  
        return redirect('nueva_venta')  
    else:
        form = ClienteForm()   
def Crear_Clientes(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()  
            messages.success(request, "Cliente creado con éxito.")
            return redirect('Clientes Listar')  
    else:
        messages.error(request, "Corrige los errores en el formulario.")
        form = ClienteForm()

def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)  

    if request.method == 'POST':
        cliente.cedula = request.POST['cedula']
        cliente.nombre = request.POST['nombre']
        cliente.direccion = request.POST['direccion']
        cliente.telefono = request.POST['telefono']
        cliente.estado = request.POST.get('estado', False) == 'on'
        cliente.save()
        messages.success(request, "Cliente actualizado con éxito.")
        return redirect('Clientes Listar')  

    return render(request, 'editar_cliente.html', {'cliente': cliente})
