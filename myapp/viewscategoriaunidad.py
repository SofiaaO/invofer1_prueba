from django.shortcuts import render, redirect
from .models import Categoria, UnidadMedida, CategoriaUnidadMedida
from .forms import CategoriaUnidadMedidaForm
from django.contrib import messages
from django.http import JsonResponse 
from django.shortcuts import get_object_or_404


def gestionar_categoria_unidades(request):
    if request.method == "POST":
        form = CategoriaUnidadMedidaForm(request.POST)
        if form.is_valid():
            categoria = form.cleaned_data['categorias']
            unidades = form.cleaned_data['unidades_medida']

            if CategoriaUnidadMedida.objects.filter(categoria=categoria).exists():
                messages.error(request, "Esta categoría ya tiene unidades de medida asignadas. Por favor, edítala.")
                return redirect('gestionar_categoria_unidades')

            for unidad in unidades:
                CategoriaUnidadMedida.objects.create(categoria=categoria, unidad_medida=unidad)

            messages.success(request, "Unidades de medida asignadas con éxito.")
            return redirect('gestionar_categoria_unidades')
    else:
        form = CategoriaUnidadMedidaForm()

    categorias_unidades = CategoriaUnidadMedida.objects.select_related('categoria', 'unidad_medida').all()

    return render(request, "categoria_unidad/categorias_unidades.html", {
        "form": form,
        "categorias_unidades": categorias_unidades,
    })


def editar_categoria_unidades(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    unidades_asociadas = CategoriaUnidadMedida.objects.filter(categoria=categoria).values_list('unidad_medida', flat=True)

    if request.method == "POST":
        unidades_seleccionadas = request.POST.getlist('unidades_medida')
        CategoriaUnidadMedida.objects.filter(categoria=categoria).delete()

        for unidad_id in unidades_seleccionadas:
            unidad = UnidadMedida.objects.get(id=unidad_id)
            CategoriaUnidadMedida.objects.create(categoria=categoria, unidad_medida=unidad)

        messages.success(request, "Unidades de medida actualizadas con éxito.")
        return redirect('gestionar_categoria_unidades')
    else:
        unidades = UnidadMedida.objects.all()
        unidades_data = [
            {
                "id": unidad.id,
                "nombre": unidad.nombre,
                "abreviatura": unidad.abreviatura,
                "seleccionada": unidad.id in unidades_asociadas
            }
            for unidad in unidades
        ]

        return JsonResponse({"unidades": unidades_data})


def obtener_unidades_categoria(request, id):
    categoria = Categoria.objects.get(id=id)
    unidades_seleccionadas = set(
        CategoriaUnidadMedida.objects.filter(categoria=categoria)
        .values_list('unidad_medida_id', flat=True)
    )

    unidades = [
        {
            "id": unidad.id,
            "nombre": unidad.nombre,
            "abreviatura": unidad.abreviatura,
            "seleccionada": unidad.id in unidades_seleccionadas
        }
        for unidad in UnidadMedida.objects.all()
    ]

    return JsonResponse({"unidades": unidades})
