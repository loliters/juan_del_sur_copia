from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id_cliente', 'nombre', 'carnet', 'email', 'telefono', 'estado')
    list_editable = ('estado',)
    search_fields = ('nombre', 'carnet', 'email', 'telefono')


