from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from myapp.models import CustomUser

@login_required
def editar_perfil(request):
    if request.method == "POST":
        nuevo_nombre = request.POST.get("nombre_usuario")
        if nuevo_nombre:
            request.user.nombre_usuario = nuevo_nombre
            request.user.save()
            messages.success(request, "Nombre de usuario actualizado correctamente.")
        else:
            messages.error(request, "El nombre de usuario no puede estar vacío.")
        return redirect("dashboard")  # Ajusta según tu vista principal

    return render(request, "editar_perfil.html", {"user": request.user})
