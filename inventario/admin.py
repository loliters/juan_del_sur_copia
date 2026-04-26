from django.contrib import admin
from .models import Inventario

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('id_inven', 'producto', 'stock_actual', 'tipoUnidad')
    search_fields = ('producto__nomProducto',)
    list_filter = ('tipoUnidad',)