from django.shortcuts import redirect, render
from myapp.models import *
from myapp.forms import * 
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
def listar_tasas_cambio(request):
    query = request.GET.get('buscar', '')
    tasas = TasaCambio.objects.all()
    form = TasaCambioForm() 

    if query:
        tasas = tasas.filter(
            Q(moneda_origen__nombre__icontains=query) | Q(moneda_destino__nombre__icontains=query))

    return render(request, 'Monedas/monedas_listar.html', {'tasas': tasas, 'form': form})

def crear_tasa_cambio(request):
    if request.method == 'POST':
        form = TasaCambioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_tasa')
    else:
        form = TasaCambioForm()
    return render(request, 'Monedas/monedas_listar.html', {'form': form})

@require_POST
def editar_tasa_cambio(request, id):
    tasa = get_object_or_404(TasaCambio, id=id)
    nueva_tasa = request.POST.get('tasa')

    if nueva_tasa:
        tasa.tasa = nueva_tasa
        tasa.save()
    
    return redirect('listar_tasa')