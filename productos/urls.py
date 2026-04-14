#rutas
from django.urls import path, include
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.inventario, name='index'),  # ← Agrega esta línea
    path('inventario/', views.inventario, name='inventario'),
    path('registrar/', views.registrar, name='registrar'),
    path('editar/<int:id_producto>/', views.editar, name='editar'),
    path('eliminar/<int:id_producto>/', views.eliminar, name='eliminar'),
]