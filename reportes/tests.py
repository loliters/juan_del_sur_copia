from django.test import TestCase, RequestFactory
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from reportes.views import filtrar_compras, exportar_compras_pdf
from compras.models import Compra, DetalleCompra
from productos.models import Producto
from categorias.models import Categoria
from proveedores.models import Proveedor
from inventario.models import Inventario

class ReportesFiltrosTests(TestCase):
    """Pruebas alineadas 1 a 1 con tu checklist"""

    def setUp(self):
        self.factory = RequestFactory()
        
        # 📦 Datos base
        self.cat = Categoria.objects.create(nomCategoria="Test Cat", estado=True)
        self.prov = Proveedor.objects.create(nomProv="Test Prov", estado=True)
        
        # ⚠️ NO pasar stockActual aquí para evitar el error del setter
        self.prod = Producto.objects.create(
            codProducto="P001", nomProducto="Test Prod",
            precioCompra=Decimal("10.00"), precioVenta=Decimal("15.00"),
            tipoUnidad="Unidad", estado="activo",
            categoria=self.cat
        )
        
        # ✅ Crear Inventario manualmente (como hace tu vista registrar)
        self.inv = Inventario.objects.create(
            producto=self.prod, stock_actual=100, tipoUnidad="Unidad"
        )
        
        today = timezone.now()
        self.comp_hoy = Compra.objects.create(
            total=Decimal("50.00"), fecha=today, estado=True, proveedor=self.prov
        )
        DetalleCompra.objects.create(
            compra=self.comp_hoy, inventario=self.inv, cantidad=5, subtotal=Decimal("50.00")
        )

    # ✅ 1. Filtro fecha estándar
    def test_1_fecha_estandar_este_mes(self):
        req = self.factory.get('/?filtro_fecha=este_mes')
        qs = filtrar_compras(req)
        self.assertGreaterEqual(qs.count(), 1)

    # ✅ 2. Filtro fecha personalizada
    def test_2_fecha_personalizada(self):
        hoy = timezone.now().date().strftime('%Y-%m-%d')
        req = self.factory.get(f'/?fecha_desde={hoy}&fecha_hasta={hoy}')
        qs = filtrar_compras(req)
        self.assertGreaterEqual(qs.count(), 1)

    # ✅ 3. Filtro combinado sin error 500
    def test_3_filtro_combinado_no_crashea(self):
        url = f'/?filtro_fecha=este_mes&producto={self.prod.pk}&categoria={self.cat.pk}&proveedor={self.prov.pk}'
        req = self.factory.get(url)
        qs = filtrar_compras(req)  # Si llega aquí sin excepción, ✅
        self.assertIsNotNone(qs)

    # ✅ 4. Exportar PDF refleja filtros (valida integridad del archivo)
    def test_4_exportar_pdf_valido(self):
        req = self.factory.get(f'/exportar/?filtro_fecha=este_mes&producto={self.prod.pk}')
        resp = exportar_compras_pdf(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF'))

    # ✅ 5. Dropdowns: ID válido e inválido (resiliente a URL manipulada)
    def test_5_dropdown_id_valido_e_invalido(self):
        # Válido
        req = self.factory.get(f'/?producto={self.prod.pk}')
        self.assertGreaterEqual(filtrar_compras(req).count(), 1)
        
        # Inválido (debe devolver 0, NO crashear)
        req = self.factory.get('/?producto=99999')
        self.assertEqual(filtrar_compras(req).count(), 0)

    # ✅ 6. Sin resultados → PDF vacío pero válido
    def test_6_pdf_sin_resultados_valido(self):
        req = self.factory.get('/exportar/?producto=99999&fecha_desde=2050-01-01')
        resp = exportar_compras_pdf(req)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b'%PDF'))