# reportes/utils.py
from fpdf import FPDF
from django.utils import timezone

class PDFReporteGeneral(FPDF):
    """Clase base para reportes generales con FPDF2"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_font('Helvetica', '', 10)
    
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'TU EMPRESA - REPORTE', 0, 1, 'C')
        self.set_font('Helvetica', '', 9)
        fecha = timezone.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 5, f'Generado: {fecha}', 0, 1, 'C')
        self.ln(3)
        self.set_draw_color(37, 99, 235)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, f'Pagina {self.page_no()}', 0, 0, 'C')
    
    def section_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(37, 99, 235)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f' {title}', 0, 1, 'L', 1)
        self.set_text_color(0, 0, 0)
        self.ln(3)
    
    def filters_box(self, filtros):
        self.set_font('Helvetica', '', 9)
        self.set_fill_color(243, 244, 246)
        self.cell(0, 6, 'Filtros aplicados:', 0, 1, 'L', 1)
        self.ln(1)
        for label, value in filtros.items():
            self.cell(45, 5, f'{label}:', 0, 0)
            self.cell(0, 5, str(value), 0, 1)
        self.ln(3)
    
    def products_table_header(self, include_profit=False):
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(37, 99, 235)
        self.set_text_color(255, 255, 255)
        
        self.cell(25, 8, 'Codigo', 1, 0, 'C', 1)
        self.cell(60, 8, 'Producto', 1, 0, 'L', 1)
        self.cell(20, 8, 'Cant.', 1, 0, 'C', 1)
        self.cell(25, 8, 'P. Unit.', 1, 0, 'R', 1)
        self.cell(25, 8, 'Subtotal', 1, 0, 'R', 1)
        if include_profit:
            self.cell(25, 8, 'Ganancia', 1, 1, 'R', 1)
        else:
            self.cell(25, 8, '', 1, 1, 'R', 1)
        
        self.set_text_color(0, 0, 0)
        self.set_font('Helvetica', '', 9)
    
    def product_row(self, producto, cantidad, precio_unit, subtotal, ganancia=None):
        cod = str(producto.get('cod', ''))[:10] if producto.get('cod') else ''
        nom = str(producto.get('nom', ''))[:40] if producto.get('nom') else ''
        
        self.cell(25, 7, cod, 1, 0, 'C')
        self.cell(60, 7, nom, 1, 0, 'L')
        self.cell(20, 7, str(cantidad), 1, 0, 'C')
        self.cell(25, 7, f"Bs {float(precio_unit):.2f}", 1, 0, 'R')
        self.cell(25, 7, f"Bs {float(subtotal):.2f}", 1, 0, 'R')
        
        if ganancia is not None:
            gan = f"Bs {float(ganancia):.2f}"
            if float(ganancia) >= 0:
                self.set_text_color(0, 150, 0)
            else:
                self.set_text_color(200, 0, 0)
            self.cell(25, 7, gan, 1, 1, 'R')
            self.set_text_color(0, 0, 0)
        else:
            self.cell(25, 7, '', 1, 1, 'R')
    
    def totals_row(self, label, value, is_grand_total=False):
        font_size = 11 if is_grand_total else 10
        font_style = 'B' if is_grand_total else ''
        self.set_font('Helvetica', font_style, font_size)
        if is_grand_total:
            self.set_text_color(37, 99, 235)
        total = f"Bs {float(value):.2f}" if value else "Bs 0.00"
        self.cell(130, 8, label, 0, 0, 'R')
        self.cell(50, 8, total, 0, 1, 'R')
        self.set_text_color(0, 0, 0)