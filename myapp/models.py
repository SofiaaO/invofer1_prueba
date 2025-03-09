
from django.contrib.auth.hashers import make_password
# Create your models here.
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
from django.db import models
from simple_history.models import HistoricalRecords
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError("El correo electrónico es obligatorio")
        extra_fields.setdefault("is_active", True)
        user = self.model(correo=self.normalize_email(correo), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(correo, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None  
    correo = models.EmailField(unique=True)
    nombre_usuario = models.CharField(max_length=100)
    fecha_ultima_sesion = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    USERNAME_FIELD = "correo"
    REQUIRED_FIELDS = ["nombre_usuario"]

    objects = CustomUserManager()

    def __str__(self):
        return self.nombre_usuario

class Cliente(models.Model):
    cedula = models.CharField(max_length=20, unique=True, null=False)  
    nombre = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nombre}"
    
class Proveedor(models.Model):
    rif = models.CharField(max_length=20, unique=True,  null=False) 
    nombre = models.CharField(max_length=100)  
    telefono = models.CharField(max_length=15,null=False)  
    direccion = models.TextField(null=False) 
    direccion_fiscal = models.TextField(null=False)
    productos_ofrecidos = models.TextField(blank=True, null=True) 
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)  
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.nombre}"

class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    estado = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.nombre

class UnidadMedida(models.Model):
    nombre = models.CharField(max_length=50)
    abreviatura = models.CharField(max_length=10)
    estado = models.BooleanField(default=True)
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.nombre

    def obtener_unidades(self):
        return self.categoria_unidades.values_list("unidad_medida__nombre", flat=True)

class CategoriaUnidadMedida(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='categoria_unidades')
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE, related_name='unidad_categorias')
    history = HistoricalRecords()
    class Meta:
        unique_together = ('categoria', 'unidad_medida')

    def __str__(self):
        return f"{self.categoria} - {self.unidad_medida}"

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE) 
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.nombre


class Presentacion(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=100, unique=True, null=False)
    categoria_unidad = models.ForeignKey(CategoriaUnidadMedida, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    stock_minimo = models.IntegerField()
    estado = models.BooleanField(default=True)
    total_neto = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.producto.nombre} - {self.valor} {self.categoria_unidad.unidad_medida.nombre}"
    
class Moneda(models.Model):
    codigo = models.CharField(max_length=3, unique=True)  # Código de la moneda (ej: USD, VES, EUR)
    nombre = models.CharField(max_length=50)  # Nombre de la moneda (ej: Dólar, Bolívar, Euro)
    simbolo = models.CharField(max_length=5, blank=True, null=True)  # Símbolo (ej: $, Bs, €)
    estado = models.BooleanField(default=True)  # Para activar/desactivar la moneda

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
    
class TasaCambio(models.Model):
    moneda_origen = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name='tasas_origen')
    moneda_destino = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name='tasas_destino')
    tasa = models.DecimalField(max_digits=10, decimal_places=4) 
    fecha = models.DateTimeField(auto_now_add=True)  

    class Meta:
        unique_together = ('moneda_origen', 'moneda_destino')  

class Ventas(models.Model):
    numero_factura = models.CharField(max_length=20, unique=True)
    id_venta = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="ventas")
    fecha_venta = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    total_bs=models.DecimalField(max_digits=10,decimal_places=2,null=True)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    history = HistoricalRecords()
    def __str__(self):
        return f"Venta {self.id_venta} - Total: {self.total}$ - Total: {self.total}Bs"

class DetalleVentas(models.Model):
    venta = models.ForeignKey(Ventas, on_delete=models.CASCADE)
    presentacion = models.ForeignKey(Presentacion, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario_bs=models.DecimalField(max_digits=10,decimal_places=2,null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_bs=models.DecimalField(max_digits=10,decimal_places=2,null=True)
    
    def __str__(self):
        return f"Detalle de Venta {self.id} - {self.presentacion.producto.nombre}"

class Compras(models.Model):
    numero_factura = models.CharField(max_length=20, unique=True)
    id_compra = models.AutoField(primary_key=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name="compras")
    fecha_compra = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    total_bs=models.DecimalField(max_digits=10,decimal_places=2,null=True)
    history = HistoricalRecords()
    def __str__(self):
        return f"Compra {self.id_compra} - Total: {self.total}$ - Total: {self.total}Bs"

class DetalleCompras(models.Model):
    compra = models.ForeignKey(Compras, on_delete=models.CASCADE)
    presentacion = models.ForeignKey(Presentacion, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario_bs=models.DecimalField(max_digits=10,decimal_places=2,null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_bs=models.DecimalField(max_digits=10,decimal_places=2,null=True)

    def __str__(self):
        return f"Detalle de Compra {self.id} - {self.presentacion.producto.nombre}"
        
class Impuesto(models.Model):
    nombre = models.CharField(max_length=100)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2) 
    estado = models.BooleanField(default=True)  
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.nombre} - {self.porcentaje}%"
            

class Movimiento(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('compra', 'Compra'),
        ('venta', 'Venta'),
        ('ajuste_entrada', 'Ajuste de Entrada'),
        ('ajuste_salida', 'Ajuste de Salida'),
    ]

    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)  # Usuario que realiza el movimiento
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)  # Solo para compras
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)  # Solo para ventas
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)  
    descripcion = models.TextField(blank=True, null=True)  # Descripción adicional
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.tipo_movimiento} - {self.fecha_movimiento}"

class DetalleMovimiento(models.Model):
    movimiento = models.ForeignKey(Movimiento, on_delete=models.CASCADE, related_name="detalles")
    presentacion = models.ForeignKey(Presentacion, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle {self.id} - Movimiento {self.movimiento.id}"
    