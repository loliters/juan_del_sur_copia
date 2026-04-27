# ventas/urls.py
from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # CRUD ventas
    path('ver/', views.ver_ventas, name='ver_ventas'),
    path('editar/<int:id>/', views.editar_venta, name='editar_venta'),
    path('eliminar/<int:id>/', views.eliminar_venta, name='eliminar_venta'),
    
    # Carrito
    path('agregar-al-carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar-del-carrito/<str:cod>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),  # ← Cambiar a <str:cod>
    path('registro-venta/', views.registro_venta, name='registro_venta'),
    path('seleccionar-cliente/', views.seleccionar_cliente, name='seleccionar_cliente'),
]