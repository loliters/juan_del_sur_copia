from django.urls import path
from . import views

app_name = 'reportes' 

urlpatterns = [
    # Ventas
    path('ventas/', views.ventas_report, name='ventas_report'),
    path('ventas/imprimir/<int:id_venta>/', views.imprimir_venta, name='imprimir_venta'),
    path('ventas/pdf/<int:id_venta>/', views.generar_pdf_venta, name='generar_pdf_venta'),
    path('ventas/exportar/', views.exportar_ventas_pdf, name='exportar_ventas_pdf'),
    
    # Compras
    path('compras/', views.compras_report, name='compras_report'),
    path('compras/imprimir/<int:id_compra>/', views.imprimir_compra, name='imprimir_compra'),
    path('compras/pdf/<int:id_compra>/', views.generar_pdf_compra, name='generar_pdf_compra'),
    path('compras/exportar/', views.exportar_compras_pdf, name='exportar_compras_pdf'),
    
    # Debug
    path('test-pdf/', views.test_pdf, name='test_pdf'),
]