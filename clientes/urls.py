# clientes/urls.py
from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # URLs existentes
    path('registro/', views.registro_cliente, name='registro_cliente'),
    path('ver/', views.ver_clientes, name='lista_clientes'),
    
    # Nuevas URLs para editar y eliminar
    path('editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),
    
    # URLs para ver clientes inactivos (borrado lógico)
    path('inactivos/', views.clientes_inactivos, name='clientes_inactivos'),
    path('restaurar/<int:id>/', views.restaurar_cliente, name='restaurar_cliente'),
]