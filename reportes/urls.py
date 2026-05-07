from django.urls import path
from . import views

urlpatterns = [
    # Reporte de Ventas (index por defecto)
    path('ventas/', views.ventas_report, name='ventas_report'),
    path('ventas/imprimir/<int:id_venta>/', views.imprimir_venta, name='imprimir_venta'),
    path('ventas/pdf/<int:id_venta>/', views.generar_pdf_venta, name='generar_pdf_venta'),
    
    # Reporte de Compras
    path('compras/', views.compras_report, name='compras_report'),
    path('compras/imprimir/<int:id_compra>/', views.imprimir_compra, name='imprimir_compra'),
    path('compras/pdf/<int:id_compra>/', views.generar_pdf_compra, name='generar_pdf_compra'),
]