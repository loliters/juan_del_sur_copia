from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, F
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime, timedelta
from fpdf import FPDF  # <-- Usamos FPDF2
import io
import os
from django.db.models import Prefetch

# Models
from ventas.models import Venta, DetalleVenta
from compras.models import Compra, DetalleCompra
from clientes.models import Cliente
from proveedores.models import Proveedor
from inventario.models import Inventario
from productos.models import Producto
from categorias.models import Categoria


def get_date_range(filter_type, custom_from=None, custom_to=None):
    """Obtiene el rango de fechas según el filtro seleccionado"""
    today = timezone.now().date()
    
    # Si hay fechas personalizadas, tienen prioridad
    if custom_from and custom_to:
        try:
            from_date = datetime.strptime(custom_from, '%Y-%m-%d').date()
            to_date = datetime.strptime(custom_to, '%Y-%m-%d').date()
            return from_date, to_date
        except:
            pass
    
    # Filtros preestablecidos
    if filter_type == 'ultimo_dia':
        return today, today
    elif filter_type == 'ultima_semana':
        return today - timedelta(days=7), today
    elif filter_type == 'este_mes':
        return today.replace(day=1), today
    elif filter_type == 'este_año':
        return today.replace(month=1, day=1), today
    
    return None, None


def filtrar_ventas(request):
    """Lógica de filtrado para ventas"""
    
    # ✅ Carga los detalles con producto relacionado
    ventas = Venta.objects.select_related('cliente', 'metodo_pago').prefetch_related(
        Prefetch('detalles', queryset=DetalleVenta.objects.select_related('inventario__producto'))
    ).all()
    
    # Filtros
    filtro_fecha = request.GET.get('filtro_fecha', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    producto_filter = request.GET.get('producto', '')
    categoria_filter = request.GET.get('categoria', '')
    
    # Filtrar por fecha
    from_date, to_date = get_date_range(filtro_fecha, fecha_desde, fecha_hasta)
    if from_date and to_date:
        ventas = ventas.filter(fecha__date__range=[from_date, to_date])
    
    # Filtrar por producto
    if producto_filter:
        if producto_filter == 'mas_vendido':
            from django.db.models import Sum
            detalles = DetalleVenta.objects.values('inventario__producto').annotate(
                total_cantidad=Sum('cantidad')
            ).order_by('-total_cantidad')
            if detalles:
                producto_id = detalles[0]['inventario__producto']
                ventas = ventas.filter(detalles__inventario__producto_id=producto_id)
        else:
            ventas = ventas.filter(detalles__inventario__producto_id=producto_filter)
    
    # Filtrar por categoría
    if categoria_filter and categoria_filter != '':
        try:
            ventas = ventas.filter(detalles__inventario__producto__categoria_id=categoria_filter)
        except:
            pass
    
    return ventas.distinct()


def filtrar_compras(request):
    """Lógica de filtrado para compras"""
    compras = Compra.objects.select_related('proveedor').all()
    
    # Filtros
    filtro_fecha = request.GET.get('filtro_fecha', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    producto_filter = request.GET.get('producto', '')
    categoria_filter = request.GET.get('categoria', '')  # Ahora será ID
    proveedor_filter = request.GET.get('proveedor', '')
    estado_inventario = request.GET.get('estado_inventario', '')
    
    # Filtrar por fecha
    from_date, to_date = get_date_range(filtro_fecha, fecha_desde, fecha_hasta)
    if from_date and to_date:
        compras = compras.filter(fecha__date__range=[from_date, to_date])
    
    # Filtrar por proveedor
    if proveedor_filter:
        compras = compras.filter(proveedor_id=proveedor_filter)
    
    # Filtrar por producto
    if producto_filter:
        if producto_filter == 'mas_comprado':
            from django.db.models import Sum
            detalles = DetalleCompra.objects.values('inventario__producto').annotate(
                total_cantidad=Sum('cantidad')
            ).order_by('-total_cantidad')
            if detalles:
                producto_id = detalles[0]['inventario__producto']
                # ✅ Usa 'detalles' (related_name)
                compras = compras.filter(detalles__inventario__producto_id=producto_id)
        else:
            # ✅ Usa 'detalles' (related_name)
            compras = compras.filter(detalles__inventario__producto_id=producto_filter)
    
    # Filtrar por categoría (ahora recibe ID)
    if categoria_filter and categoria_filter != '':
        try:
            # ✅ Usa 'detalles' (related_name)
            compras = compras.filter(detalles__inventario__producto__categoria_id=categoria_filter)
        except:
            pass
    
    # Filtrar por estado en inventario
    if estado_inventario:
        if estado_inventario == 'agotado':
            compras = compras.filter(detalles__inventario__stock_actual=0)
        elif estado_inventario == 'bajo_stock':
            compras = compras.filter(
                detalles__inventario__stock_actual__lte=F('detalles__inventario__producto__stockMinimo')
            )
    
    return compras.distinct()


def ventas_report(request):
    """Vista principal del reporte de ventas"""
    ventas = filtrar_ventas(request)
    
    # Calcular totales
    total_vendido = ventas.aggregate(total=Sum('total'))['total'] or 0
    cant_ventas = ventas.count()
    
    # Datos para filtros
    productos = Producto.objects.filter(estado='activo').select_related('categoria')
    categorias = Categoria.objects.filter(estado=True)
    clientes = Cliente.objects.filter(estado=True)
    
    # Fecha del reporte
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    filtro_fecha = request.GET.get('filtro_fecha', '')
    
    # Determinar rango de fechas para mostrar
    from_date, to_date = get_date_range(filtro_fecha, fecha_desde, fecha_hasta)
    if from_date and to_date:
        fecha_reporte = f"{from_date.strftime('%Y-%m-%d')} - {to_date.strftime('%Y-%m-%d')}"
    else:
        fecha_reporte = "Todos los registros"
    
    context = {
        'ventas': ventas,
        'total_vendido': total_vendido,
        'cant_ventas': cant_ventas,
        'fecha_reporte': fecha_reporte,
        'productos': productos,
        'categorias': categorias,
        'clientes': clientes,
        'filtro_fecha': filtro_fecha,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'reportes/ventas_report.html', context)


def compras_report(request):
    """Vista principal del reporte de compras"""
    compras = filtrar_compras(request)
    
    # Calcular totales
    total_comprado = compras.aggregate(total=Sum('total'))['total'] or 0
    ordenes_realizadas = compras.count()
    
    # Datos para filtros
    productos = Producto.objects.filter(estado='activo').select_related('categoria')
    categorias = Categoria.objects.filter(estado=True)
    proveedores = Proveedor.objects.filter(estado=True)
    
    # Fecha del reporte
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    filtro_fecha = request.GET.get('filtro_fecha', '')
    
    # Determinar rango de fechas para mostrar
    from_date, to_date = get_date_range(filtro_fecha, fecha_desde, fecha_hasta)
    if from_date and to_date:
        fecha_reporte = f"{from_date.strftime('%Y-%m-%d')} - {to_date.strftime('%Y-%m-%d')}"
    else:
        fecha_reporte = "Todos los registros"
    
    context = {
        'compras': compras,
        'total_comprado': total_comprado,
        'ordenes_realizadas': ordenes_realizadas,
        'fecha_reporte': fecha_reporte,
        'productos': productos,
        'categorias': categorias,
        'proveedores': proveedores,
        'filtro_fecha': filtro_fecha,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'reportes/compras_report.html', context)

class PDFVenta(FPDF):
    """Clase PDF personalizada para facturas de venta"""
    
    def header(self):
        # Logo o nombre de empresa
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'TU EMPRESA', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'NIT: 1234567890', 0, 1, 'C')
        self.ln(5)
        
        # Título del documento
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'FACTURA DE VENTA', 0, 1, 'C')
        self.ln(5)
        
        # Línea separadora
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
    
    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, 'Gracias por su compra', 0, 0, 'C')
        self.ln(4)
        self.cell(0, 5, f'Impreso: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 0, 'C')
    
    def section_title(self, title):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(37, 99, 235)  # Azul
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f' {title}', 0, 1, 'L', 1)
        self.set_text_color(0, 0, 0)
        self.ln(2)
    
    def info_row(self, label, value):
        self.set_font('Arial', 'B', 9)
        self.cell(40, 5, f'{label}:', 0, 0)
        self.set_font('Arial', '', 9)
        self.cell(0, 5, str(value), 0, 1)


def generar_pdf_venta(request, id_venta):
    """Generar PDF de venta usando FPDF2"""
    venta = get_object_or_404(
        Venta.objects.select_related('cliente', 'metodo_pago'), 
        id_venta=id_venta
    )
    detalles = DetalleVenta.objects.select_related(
        'inventario__producto'
    ).filter(venta=venta)
    
    # Crear PDF
    pdf = PDFVenta()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Información del cliente
    cliente = venta.cliente
    pdf.section_title('Información del Cliente')
    pdf.info_row('Nombre', cliente.nombre)
    if cliente.razonSocial:
        pdf.info_row('Razón Social', cliente.razonSocial)
    pdf.info_row('Carnet', cliente.carnet)
    pdf.info_row('Teléfono', cliente.telefono)
    pdf.info_row('Email', cliente.email)
    pdf.info_row('Dirección', f"{cliente.zona}, {cliente.calle} #{cliente.numeroCasa}")
    pdf.ln(3)
    
    # Información de la venta
    pdf.section_title('Información de la Venta')
    pdf.info_row('Número de Venta', f"#{venta.id_venta}")
    pdf.info_row('Fecha', venta.fecha.strftime("%d/%m/%Y %H:%M"))
    pdf.info_row('Método de Pago', venta.metodo_pago.tipoPago)
    pdf.ln(5)
    
    # Tabla de detalles
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    
    # Encabezados de tabla
    pdf.cell(25, 8, 'Código', 1, 0, 'C', 1)
    pdf.cell(70, 8, 'Producto', 1, 0, 'L', 1)
    pdf.cell(20, 8, 'Cant.', 1, 0, 'C', 1)
    pdf.cell(30, 8, 'Precio Unit.', 1, 0, 'R', 1)
    pdf.cell(30, 8, 'Subtotal', 1, 1, 'R', 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    
    # Filas de detalles
    for detalle in detalles:
        producto = detalle.inventario.producto
        pdf.cell(25, 7, producto.codProducto or '', 1, 0, 'C')
        pdf.cell(70, 7, producto.nomProducto[:35], 1, 0, 'L')
        pdf.cell(20, 7, str(detalle.cantidad), 1, 0, 'C')
        pdf.cell(30, 7, f"Bs {producto.precioVenta:.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"Bs {detalle.subtotal:.2f}", 1, 1, 'R')
    
    # Total
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(145, 10, 'TOTAL:', 0, 0, 'R')
    pdf.set_text_color(37, 99, 235)
    pdf.cell(40, 10, f"Bs {venta.total:.2f}", 0, 1, 'R')
    pdf.set_text_color(0, 0, 0)
    
    # Firmas
    pdf.ln(20)
    pdf.set_font('Arial', '', 9)
    pdf.cell(90, 10, '_________________________', 0, 0, 'C')
    pdf.cell(90, 10, '_________________________', 0, 1, 'C')
    pdf.cell(90, 5, 'Firma del Cliente', 0, 0, 'C')
    pdf.cell(90, 5, 'Firma del Vendedor', 0, 1, 'C')
    
    # Generar respuesta
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="venta_{id_venta}.pdf"'
    
    pdf_output = pdf.output(dest='S').encode('latin-1', errors='ignore')
    response.write(pdf_output)
    
    return response


class PDFCompra(FPDF):
    """Clase PDF personalizada para órdenes de compra"""
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'TU EMPRESA', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'NIT: 1234567890', 0, 1, 'C')
        self.ln(5)
        
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'ORDEN DE COMPRA', 0, 1, 'C')
        self.ln(5)
        
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
    
    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, 'Documento de compra oficial', 0, 0, 'C')
        self.ln(4)
        self.cell(0, 5, f'Impreso: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 0, 'C')
    
    def section_title(self, title):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(37, 99, 235)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f' {title}', 0, 1, 'L', 1)
        self.set_text_color(0, 0, 0)
        self.ln(2)
    
    def info_row(self, label, value):
        self.set_font('Arial', 'B', 9)
        self.cell(40, 5, f'{label}:', 0, 0)
        self.set_font('Arial', '', 9)
        self.cell(0, 5, str(value), 0, 1)


def generar_pdf_compra(request, id_compra):
    """Generar PDF de compra usando FPDF2"""
    compra = get_object_or_404(
        Compra.objects.select_related('proveedor'), 
        id_compra=id_compra
    )
    detalles = DetalleCompra.objects.select_related(
        'inventario__producto'
    ).filter(compra=compra)
    
    # Crear PDF
    pdf = PDFCompra()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Información del proveedor
    proveedor = compra.proveedor
    pdf.section_title('Información del Proveedor')
    pdf.info_row('Nombre', proveedor.nomProv)
    pdf.info_row('Dirección', proveedor.direccion)
    pdf.info_row('Teléfono', proveedor.telefono)
    pdf.info_row('Email', proveedor.email)
    pdf.ln(3)
    
    # Información de la compra
    pdf.section_title('Información de la Compra')
    pdf.info_row('Número de Compra', f"#{compra.id_compra}")
    pdf.info_row('Fecha', compra.fecha.strftime("%d/%m/%Y %H:%M"))
    pdf.info_row('Estado', 'Activa' if compra.estado else 'Inactiva')
    pdf.ln(5)
    
    # Tabla de detalles
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    
    pdf.cell(25, 8, 'Código', 1, 0, 'C', 1)
    pdf.cell(70, 8, 'Producto', 1, 0, 'L', 1)
    pdf.cell(20, 8, 'Cant.', 1, 0, 'C', 1)
    pdf.cell(30, 8, 'Precio Unit.', 1, 0, 'R', 1)
    pdf.cell(30, 8, 'Subtotal', 1, 1, 'R', 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    
    for detalle in detalles:
        producto = detalle.inventario.producto
        subtotal = detalle.cantidad * producto.precioCompra
        pdf.cell(25, 7, producto.codProducto or '', 1, 0, 'C')
        pdf.cell(70, 7, producto.nomProducto[:35], 1, 0, 'L')
        pdf.cell(20, 7, str(detalle.cantidad), 1, 0, 'C')
        pdf.cell(30, 7, f"Bs {producto.precioCompra:.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"Bs {subtotal:.2f}", 1, 1, 'R')
    
    # Total
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(145, 10, 'TOTAL:', 0, 0, 'R')
    pdf.set_text_color(37, 99, 235)
    pdf.cell(40, 10, f"Bs {compra.total:.2f}", 0, 1, 'R')
    pdf.set_text_color(0, 0, 0)
    
    # Firmas
    pdf.ln(20)
    pdf.set_font('Arial', '', 9)
    pdf.cell(90, 10, '_________________________', 0, 0, 'C')
    pdf.cell(90, 10, '_________________________', 0, 1, 'C')
    pdf.cell(90, 5, 'Firma del Proveedor', 0, 0, 'C')
    pdf.cell(90, 5, 'Resp. de Compras', 0, 1, 'C')
    
    # Generar respuesta
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="compra_{id_compra}.pdf"'
    
    pdf_output = pdf.output(dest='S').encode('latin-1', errors='ignore')
    response.write(pdf_output)
    
    return response


# Las funciones de imprimir (HTML) se mantienen igual
def imprimir_venta(request, id_venta):
    """Vista para imprimir venta en formato HTML"""
    venta = get_object_or_404(
        Venta.objects.select_related('cliente', 'metodo_pago'), 
        id_venta=id_venta
    )
    detalles = DetalleVenta.objects.select_related(
        'inventario__producto'
    ).filter(venta=venta)
    
    context = {
        'venta': venta,
        'detalles': detalles,
        'cliente': venta.cliente,
        'fecha_impresion': timezone.now()
    }
    
    html_string = render_to_string('reportes/venta_print.html', context)
    return HttpResponse(html_string)


def imprimir_compra(request, id_compra):
    """Vista para imprimir compra en formato HTML"""
    compra = get_object_or_404(
        Compra.objects.select_related('proveedor'), 
        id_compra=id_compra
    )
    detalles = DetalleCompra.objects.select_related(
        'inventario__producto'
    ).filter(compra=compra)
    
    context = {
        'compra': compra,
        'detalles': detalles,
        'proveedor': compra.proveedor,
        'fecha_impresion': timezone.now()
    }
    
    html_string = render_to_string('reportes/compra_print.html', context)
    return HttpResponse(html_string)