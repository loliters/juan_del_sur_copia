# productos/admin.py
from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codProducto', 'nomProducto', 'precioVenta', 'stockActual', 'stockMinimo', 'estado')
    list_editable = ('estado',)
    search_fields = ('nomProducto', 'codProducto')
    list_filter = ('estado', 'categoria')