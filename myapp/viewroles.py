from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.contrib import messages
from myapp.models import CustomUser
from django.contrib.auth.forms import UserCreationForm


@login_required
@permission_required('auth.change_group', raise_exception=True)
def asignar_roles(request):

    usuarios = CustomUser.objects.all()
    grupos = Group.objects.all()

    if request.method == 'POST':
        user_id = request.POST['user_id']  
        group_id = request.POST['group_id']  

        try:
            usuario = CustomUser.objects.get(id=user_id)  
            grupo = Group.objects.get(id=group_id)  

            usuario.groups.clear()  
            usuario.groups.add(grupo)  

            messages.success(request, f"Se asignó el rol '{grupo.name}' a {usuario.nombre_usuario}")
            return redirect('asignar_roles')  

        except CustomUser.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
        except Group.DoesNotExist:
            messages.error(request, "Grupo no encontrado.")
    
    return render(request, 'admin/asignar_roles.html', {'usuarios': usuarios, 'grupos': grupos})

@login_required
@permission_required('auth.change_permission', raise_exception=True)
def modificar_permisos(request):
    grupos = Group.objects.all()
    permisos = Permission.objects.all()
    grupo_seleccionado = None

    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        if group_id:
            grupo_seleccionado = Group.objects.get(id=group_id)

        if 'permisos' in request.POST: 
            permisos_seleccionados = request.POST.getlist('permisos')
            grupo_seleccionado.permissions.set(permisos_seleccionados)
            messages.success(request, f"Permisos actualizados para {grupo_seleccionado.name}")
            return redirect('modificar_permisos')

    return render(request, 'admin/permisos.html', {
        'grupos': grupos,
        'permisos': permisos,
        'grupo_seleccionado': grupo_seleccionado
    })
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['correo', 'nombre_usuario', 'password1', 'password2']

@login_required
def crear_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado exitosamente.")
            return redirect('crear_usuario')
    else:
        form = CustomUserCreationForm()

    return render(request, 'admin/crear_usuario.html', {'form': form})

@login_required
@permission_required('auth.add_group', raise_exception=True)
def crear_grupo(request):
    permisos = Permission.objects.all()

    if request.method == 'POST':
        nombre_grupo = request.POST.get('nombre_grupo')
        permisos_seleccionados = request.POST.getlist('permisos')

        if nombre_grupo:
            grupo, creado = Group.objects.get_or_create(name=nombre_grupo)
            grupo.permissions.set(permisos_seleccionados)
            messages.success(request, f"Grupo '{nombre_grupo}' creado correctamente.")
            return redirect('crear_grupo')
        else:
            messages.error(request, "Debe proporcionar un nombre para el grupo.")

    return render(request, 'admin/crear_grupo.html', {'permisos': permisos})
