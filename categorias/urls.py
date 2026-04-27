from django.urls import path
from . import views

app_name = 'categorias'

urlpatterns = [
    path('', views.lista_categorias, name='lista'),
    path('crear/', views.crear_categoria, name='crear'),
    path('editar/<int:id_categoria>/', views.editar_categoria, name='editar'),
    path('eliminar/<int:id_categoria>/', views.eliminar_categoria, name='eliminar'),

    # opcional
    path('inactivas/', views.lista_inactivas, name='inactivas'),
    path('recuperar/<int:id_categoria>/', views.recuperar_categoria, name='recuperar'),

    path('lista/', views.lista_categorias, name='lista_categorias'),
]