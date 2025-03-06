from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Impuesto
from .forms import ImpuestoForm

def gestionar_impuestos(request, id=None):
    query = request.GET.get('buscar', '')
    if query: 
        impuestos_list = Impuesto.objects.filter(nombre__icontains=query).order_by('nombre') 
    else: 
        impuestos_list= Impuesto.objects.all().order_by('nombre') 
    paginator = Paginator(impuestos_list, 5)
    page_number = request.GET.get('page')
    impuestos = paginator.get_page(page_number)

    if request.method == 'POST':
        if id:
            impuesto = get_object_or_404(Impuesto, id=id)
            form = ImpuestoForm(request.POST, instance=impuesto)
            mensaje = "Impuesto actualizado con éxito"
        else:
            form = ImpuestoForm(request.POST)
            mensaje = "Impuesto creado con éxito"
        if form.is_valid():
            form.save()
            messages.success(request, mensaje)
            return redirect('Gestionar Impuestos')
    else:
        if id:
            impuesto = get_object_or_404(Impuesto, id=id)
            form = ImpuestoForm(instance=impuesto)
        else:
            form = ImpuestoForm()

    return render(request, 'Impuestos/impuestos.html', {
        'impuestos': impuestos,
        'form': form,
    })

def eliminar_impuesto(request, id):
    impuesto = get_object_or_404(Impuesto, id=id)
    impuesto.delete()
    messages.success(request, "Impuesto eliminado con éxito")
    return redirect('Gestionar Impuestos')
