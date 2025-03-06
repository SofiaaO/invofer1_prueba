from django.urls import path
from myapp.viewscliente import *
from myapp.viewslogin import *
from myapp.viewsproducto import *
from myapp.viewscategoria import *
from myapp.viewsunidad import *
from myapp.viewsventas import *
from myapp.viewsproveedor import *
from myapp.viewsimpuestos import *
from myapp.viewscategoriaunidad import *
from myapp.viewsmarca import *
from myapp.viewroles import *
from myapp.viewsperfil import *
from myapp.viewsmovimiento import *
from myapp.viewscompra import *
urlpatterns = [
    path('', login_view, name="login"),
    path('logout/', logout_view, name="logout"),
    path('dashboard/', dashboard, name="dashboard"),
    path('crear_usuario/', crear_usuario, name='crear_usuario'),
    path('crear_grupo/', crear_grupo, name='crear_grupo'),
    path('asignar_roles/', asignar_roles, name='asignar_roles'),
    path('modificar_permisos/', modificar_permisos, name='modificar_permisos'),
    path("editar-perfil/", editar_perfil, name="editar_perfil"),
    path('Clientes/', listar_clientes, name="Clientes Listar"),
    path('Clientes/crear', Crear_Clientes, name="Crear Clientes"),
    path('Clientes/editar/<int:id>/', editar_cliente, name='Editar Clientes'),
    path('Proveedores/', listar_proveedores, name="Proveedor Listar"),
    path('Proveedores/crear', Crear_Proveedor, name="Crear Proveedor"),
    path('Proveedores/editar/<int:id>/', editar_proveedor, name='Editar Proveedor'),
    path('productos/', listar_productos, name='lista_productos'),
    path('productos/crear/', crear_producto, name="agregar"), 
    path('productos/editar/<int:id>/', editar_producto, name='editar_producto'),
    path('productos/nuevo/', crear_presentacion, name='crear_presentacion'),
    path('obtener_unidades_por_producto/<int:producto_id>/', obtener_unidades_por_producto, name='obtener_unidades_por_producto'),
    path('listar_presentaciones/', listar_presentaciones, name='listar_presentaciones'),
    path('movimientos/', listar_movimientos, name='listar_movimientos'),
    path('categorias/', gestionar_categorias, name='Gestionar Categorias'),  
    path('categorias/<int:id>/', gestionar_categorias, name='Editar Categoria'),
    path('marcas/', gestionar_marcas, name='Gestionar Marcas'),
    path('marcas/<int:id>/', gestionar_marcas, name='Editar Marca'),
    path('unidades/', gestionar_unidades, name='Gestionar Unidades'),
    path('unidades/<int:id>/', gestionar_unidades, name='Editar Unidad'),
    path('login/', login, name='Login'),
    path('compras/', listar_compras, name='compras_listar'),
    path('compras/nueva/', nueva_compra, name='nueva_compra'),
    path('compras/editar-cantidad/', editar_cantidad, name='editar_cantidad'),
    path('compras/agregar/', agregar_producto_compra, name='agregar_producto_compra'),
    path('compras/eliminar/', eliminar_producto_compra, name='eliminar_producto_compra'),
    path('compras/guardar/', guardar_compra, name='guardar_compra'),
    path('compras/comprobante/<int:id_compra>/', generar_comprobante_compra_pdf, name='generar_comprobante_compra_pdf'),
    path('compras/crear-proveedor/', Crear_Proveedores2, name='crear_proveedor'),
    path('compras/detalle/<int:id_compra>/', detalle_compra, name='detalle_compra'),
    path('ventas/', listar_ventas, name='ventas_listar'),
    path('ventas/nueva/', nueva_venta, name='nueva_venta'),
    path('ventas/editar-cantidad/', editar_cantidad_ventas, name='editar_cantidad'),
    path('ventas/agregar-producto/', agregar_producto, name='agregar_producto'),
    path('ventas/eliminar-producto/', eliminar_producto, name='eliminar_producto'),
    path('ventas/guardar/', guardar_venta, name='guardar_venta'),
    path('factura/pdf/<int:id_venta>/', generar_factura_pdf, name='generar_factura_pdf'),
    path('ventas/crear-cliente/', Crear_Clientes2, name='crear_cliente'),
    path('ventas/detalle/<int:id_venta>/', detalle_venta, name='detalle_venta'),
    path("categorias/unidades/", gestionar_categoria_unidades, name="gestionar_categoria_unidades"),
    path("obtener-unidades-categoria/<int:id>/", obtener_unidades_categoria, name="obtener_unidades_categoria"),
    path("editar-categoria-unidades/<int:id>/", editar_categoria_unidades, name="editar_categoria_unidades"),
    path('impuestos/', gestionar_impuestos, name='Gestionar Impuestos'),  
    path('impuestos/<int:id>/', gestionar_impuestos, name='Editar Impuesto'),
    path('impuestos/eliminar/<int:id>/', eliminar_impuesto, name='eliminar_impuesto'),
]
