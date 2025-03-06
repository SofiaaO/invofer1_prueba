from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import UnidadMedida
from .forms import UnidadMedidaForm
from django.db.models import Q

def gestionar_unidades(request, id=None):
    query = request.GET.get('buscar', '')
    
    if query: 
        unidades_list = UnidadMedida.objects.filter(
        Q(nombre__icontains=query) | Q(abreviatura__icontains=query)
    ).order_by('nombre')  
    else:
        unidades_list=UnidadMedida.objects.all().order_by('nombre') 

    paginator = Paginator(unidades_list, 5)
    page_number = request.GET.get('page')
    unidades = paginator.get_page(page_number)

    if request.method == 'POST':
        if id:
            unidad = get_object_or_404(UnidadMedida, id=id)
            form = UnidadMedidaForm(request.POST, instance=unidad)
            mensaje = "Unidad actualizada con éxito"
        else:
            form = UnidadMedidaForm(request.POST)
            mensaje = "Unidad creada con éxito"
        if form.is_valid():
            form.save()
            messages.success(request, mensaje)
            return redirect('Gestionar Unidades')
    else:
        if id:
            unidad = get_object_or_404(UnidadMedida, id=id)
            form = UnidadMedidaForm(instance=unidad)
        else:
            form = UnidadMedidaForm()

    return render(request, 'unidades/unidades_list.html', {
        'unidades': unidades,
        'form': form,
    })