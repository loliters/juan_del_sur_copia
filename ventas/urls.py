# ventas/urls.py
from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    # CRUD ventas
    path('ver/', views.ver_ventas, name='ver_ventas'),
    path('editar/<int:id>/', views.editar_venta, name='editar_venta'),
    path('eliminar/<int:id>/', views.eliminar_venta, name='eliminar_venta'),
    
    # Ventas
    path('registro-venta/', views.registro_venta, name='registro_venta'),
    path('seleccionar-cliente/', views.seleccionar_cliente, name='seleccionar_cliente'),
    
    # AJAX endpoints para carrito (ESTAS 3 SON LAS IMPORTANTES)
    path('agregar-al-carrito/', views.agregar_al_carrito_ajax, name='agregar_al_carrito'),
    path('actualizar-cantidad/', views.actualizar_cantidad_carrito, name='actualizar_cantidad_carrito'),
    path('eliminar-del-carrito/', views.eliminar_del_carrito_ajax, name='eliminar_del_carrito'),
]