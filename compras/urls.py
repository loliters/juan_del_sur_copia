from django.urls import path
from . import views

app_name = 'compras'

urlpatterns = [
    path('', views.ver_compras, name='ver_compras'),
    path('crear/', views.crear_compra, name='crear_compra'),
    path('editar/<int:id>/', views.editar_compra, name='editar_compra'),
    path('eliminar/<int:id>/', views.eliminar_compra, name='eliminar_compra'),
    path('desactivadas/', views.compras_eliminadas, name='compras_desactivadas'),
    path('activar/<int:id>/', views.activar_compra, name='activar_compra'),

    path('<int:id_compra>/detalle/', views.detalle_compra, name='detalle_compra'),
    # AJAX
    path('ajax/agregar-carrito/', views.agregar_al_carrito_compra_ajax, name='agregar_carrito_ajax'),
    path('ajax/actualizar-cantidad/', views.actualizar_cantidad_carrito_compra, name='actualizar_cantidad_ajax'),
    path('ajax/eliminar-carrito/', views.eliminar_del_carrito_compra_ajax, name='eliminar_carrito_ajax'),
    path('ajax/buscar-productos/', views.buscar_productos_compra_ajax, name='buscar_productos_ajax'),
]