from django import forms
from .models import *
from django.contrib.auth.forms import AuthenticationForm

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la cédula'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ingrese la dirección', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el teléfono'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'rif': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el RIF'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el teléfono'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ingrese la dirección', 'rows': 3}),
            'direccion_fiscal': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ingrese la dirección fiscal', 'rows': 3}),
            'productos_ofrecidos': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Productos ofrecidos', 'rows': 2}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    

class LoginForm(AuthenticationForm):
    correo = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['username'] 

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
class UnidadMedidaForm(forms.ModelForm):
    class Meta:
        model = UnidadMedida
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'abreviatura': forms.TextInput(attrs={'class': 'form-input'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
class CategoriaUnidadMedidaForm(forms.Form):
    categorias = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        label="Categoría",  
        widget=forms.Select()
    )
    unidades_medida = forms.ModelMultipleChoiceField(
        queryset=UnidadMedida.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        label="Unidades de Medida"
    )
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria','marca', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PresentacionForm(forms.ModelForm):
    class Meta:
        model = Presentacion
        fields = ['producto', 'codigo', 'categoria_unidad', 'valor', 'precio_venta', 'precio_compra', 'stock', 'stock_minimo', 'estado']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),  
            'categoria_unidad': forms.Select(attrs={'class': 'form-control', 'id': 'id_categoria_unidad'}),  
            'valor': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['tipo_movimiento', 'descripcion']

class DetalleMovimientoForm(forms.ModelForm):
    class Meta:
        model = DetalleMovimiento
        fields = ['presentacion', 'cantidad', 'precio_unitario']

      
class ImpuestoForm(forms.ModelForm):
    class Meta:
        model = Impuesto
        fields = ['nombre', 'porcentaje', 'estado']

class MonedaForm(forms.ModelForm):
    class Meta:
        model = Moneda
        fields = ['codigo', 'nombre', 'simbolo', 'estado']



class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['moneda_origen', 'moneda_destino', 'tasa']
        widgets = {
            'moneda_origen': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Selecciona la moneda origen'}),
            'moneda_destino': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Selecciona la moneda destino'}),
            'tasa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ingresa la tasa de cambio'}),
        }
        labels = {
            'moneda_origen': 'Moneda de origen',
            'moneda_destino': 'Moneda de destino',
            'tasa': 'Tasa de cambio',
        }
        help_texts = {
            'tasa': 'La tasa debe ser un valor numérico con hasta dos decimales.',
        }

    # Validación personalizada si fuera necesario
    def clean_tasa(self):
        tasa = self.cleaned_data.get('tasa')
        if tasa <= 0:
            raise forms.ValidationError('La tasa de cambio debe ser mayor que cero.')
        return tasa