from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from myapp.forms import LoginForm
from myapp.models import CustomUser,Presentacion, Ventas, Compras, Cliente
from django.utils import timezone
from django.contrib.auth.models import Permission
from django.contrib.auth.decorators import login_required, permission_required
from .forms import LoginForm
from django.views.decorators.cache import never_cache
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            correo = form.cleaned_data['correo']
            password = form.cleaned_data['password']

            user = authenticate(request, username=correo, password=password)

            if user is not None:
                login(request, user)
                user.fecha_ultima_sesion = timezone.now()
                user.save(update_fields=['fecha_ultima_sesion'])

                return redirect('dashboard')
            else:
                messages.error(request, "Correo o contraseña incorrectos")
        else:
            messages.error(request, "Formulario inválido")
    else:
        form = LoginForm()

    return render(request, 'Login/login.html', {'form': form})

@never_cache
def logout_view(request):
    logout(request)
    response = redirect('login')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@login_required
def dashboard(request):
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrador').exists()

    inventario_neto = sum(presentacion.precio_venta * presentacion.stock for presentacion in Presentacion.objects.all())
    productos_en_stock = Presentacion.objects.count()

    ventas_totales = sum(venta.total for venta in Ventas.objects.filter(fecha_venta__year=2025))
    facturas_emitidas = Ventas.objects.filter(fecha_venta__year=2025).count()

    compras_totales = sum(compra.total for compra in Compras.objects.filter(fecha_compra__year=2025))
    compras_realizadas = Compras.objects.filter(fecha_compra__year=2025).count()

    total_clientes = Cliente.objects.count()
    clientes_nuevos = Cliente.objects.filter(fecha_registro__year=2025).count()

    context = {
        'user': request.user,
        'is_admin': is_admin,
        'inventario_neto': inventario_neto,
        'productos_en_stock': productos_en_stock,
        'ventas_totales': ventas_totales,
        'facturas_emitidas': facturas_emitidas,
        'compras_totales': compras_totales,
        'compras_realizadas': compras_realizadas,
        'total_clientes': total_clientes,
        'clientes_nuevos': clientes_nuevos,
    }

    return render(request, 'home.html', context)


@permission_required('auth.change_permission', raise_exception=True)
def manage_permissions(request):
    users = CustomUser.objects.all()
    permissions = Permission.objects.all()

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        selected_permissions = request.POST.getlist('permissions')

        user = CustomUser.objects.get(id=user_id)
        user.user_permissions.set(selected_permissions)  # Asignar permisos seleccionados
        user.save()

        return redirect('manage_permissions')

    return render(request, 'admin/permisos.html', {'users': users, 'permissions': permissions})
