from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Categoria
from .forms import CategoriaForm
from django.contrib import messages
def gestionar_categorias(request, id=None):
    query = request.GET.get('buscar', '')
    if query:
        categorias_list = Categoria.objects.filter(nombre__icontains=query).order_by('nombre')
    else:
        categorias_list = Categoria.objects.all().order_by('nombre')  # Ordena por el campo 'nom
    paginator = Paginator(categorias_list, 5)
    page_number = request.GET.get('page')
    categorias = paginator.get_page(page_number)

    if request.method == 'POST':
        if id:
            categoria = get_object_or_404(Categoria, id=id)
            form = CategoriaForm(request.POST, instance=categoria)
            mensaje = "Categoria actualizada con éxito"
        else:
            form = CategoriaForm(request.POST)
            mensaje = "Categoria creada con éxito"
        if form.is_valid():
            form.save()
            messages.success(request, mensaje) 
            return redirect('Gestionar Categorias')
    else:
        if id:
            categoria = get_object_or_404(Categoria, id=id)
            form = CategoriaForm(instance=categoria)
        else:
            form = CategoriaForm()

    return render(request, 'categorias/categorias_list.html', {
        'categorias': categorias,
        'form': form,
    })