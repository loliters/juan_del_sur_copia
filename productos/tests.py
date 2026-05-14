from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from productos.models import Producto
from categorias.models import Categoria
from inventario.models import Inventario

class ProductosTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Simular sesión activa
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()
        
        self.cat_activa = Categoria.objects.create(nomCategoria="Activa", estado=True)
        self.cat_inactiva = Categoria.objects.create(nomCategoria="Inactiva", estado=False)
        self.prod1 = Producto.objects.create(
            codProducto="P001", nomProducto="Arroz", categoria=self.cat_activa,
            precioCompra=10.00, precioVenta=15.00, estado='activo', tipoUnidad="Kilos"
        )
        Inventario.objects.create(producto=self.prod1, stock_actual=50, tipoUnidad="Kilos")

    # 1️⃣ Listado solo muestra productos con estado=True
    def test_listado_solo_muestra_activos(self):
        Producto.objects.create(codProducto="P002", nomProducto="Frijol", categoria=self.cat_activa, estado='inactivo')
        resp = self.client.get('/productos/inventario/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Arroz")
        self.assertNotContains(resp, "Frijol")

    # 2️⃣ Formulario crear/editar carga categorías activas correctamente
    def test_formulario_carga_categorias_activas(self):
        resp = self.client.get('/productos/registrar/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Activa")
        self.assertNotContains(resp, "Inactiva")

    # 3️⃣ Formulario de editar recupera los datos correctamente
    def test_formulario_editar_recupera_datos(self):
        resp = self.client.get(f'/productos/editar/{self.prod1.id}/')
        self.assertEqual(resp.status_code, 200)

        # Verificar nombre (sin problemas de formato)
        self.assertContains(resp, "Arroz")

        # Manejar formato con coma o punto
        precio_compra = str(self.prod1.precioCompra)  # "10.0"
        precio_compra_coma = precio_compra.replace('.', ',')  # "10,0"
        precio_compra_coma_dos = f"{self.prod1.precioCompra:.2f}".replace('.', ',')  # "10,00"

        # El HTML debe contener AL MENOS uno de los formatos
        contenido = resp.content.decode('utf-8')
        self.assertTrue(
            precio_compra in contenido or 
            precio_compra_coma in contenido or 
            precio_compra_coma_dos in contenido,
            f"Precio no encontrado. Busqué: {precio_compra}, {precio_compra_coma}, {precio_compra_coma_dos}"
        )

        # Verificar que el campo tiene el valor correcto (más robusto)
        from django.test.html import parse_html
        html = parse_html(resp.content.decode('utf-8'))
        # O simplemente verificar que el value está en el HTML crudo:
        self.assertIn('name="precioCompra"', contenido)
        self.assertIn('value="10,00"', contenido)  # Formato exacto que usa tu template


    # 4️⃣ Validaciones: código único, nombre requerido
    def test_validacion_codigo_unico(self):
        from django.db import IntegrityError

        # Intentar crear producto con código duplicado
        prod2 = Producto(
            codProducto="P001",  # ← Mismo código que self.prod1
            nomProducto="Duplicado", 
            categoria=self.cat_activa, 
            precioCompra=5, 
            precioVenta=8, 
            estado='activo'
        )

        # Debe lanzar IntegrityError al hacer save()
        with self.assertRaises(IntegrityError):
            prod2.save()

        def test_validacion_nombre_requerido(self):
            resp = self.client.post('/productos/registrar/', {
                'codProducto': 'P999', 'nomProducto': '', 'categoria': self.cat_activa.id,
                'precioCompra': '5', 'precioVenta': '8', 'tipoUnidad': 'Kilos'
            })
            self.assertEqual(resp.status_code, 302)  # Redirige por error
            self.assertIn('El nombre es obligatorio', str(resp.wsgi_request._messages))

    # 5️⃣ Soft delete: estado=False oculta producto, pero permite recuperarlo
    def test_soft_delete_oculta_producto(self):
        self.client.post(f'/productos/eliminar/{self.prod1.id}/')
        self.prod1.refresh_from_db()
        self.assertEqual(self.prod1.estado, 'inactivo')
        resp_list = self.client.get('/productos/inventario/')
        self.assertNotContains(resp_list, "Arroz")

    # 6️⃣ Recuperar producto restaura visibilidad en dropdowns y listados
    def test_recuperar_restaura_visibilidad(self):
        self.prod1.estado = 'inactivo'
        self.prod1.save()
        self.client.post(f'/productos/recuperar/{self.prod1.id}/')
        self.prod1.refresh_from_db()
        self.assertEqual(self.prod1.estado, 'activo')
        resp_list = self.client.get('/productos/inventario/')
        self.assertContains(resp_list, "Arroz")

#pruebas de stock, hasta mientras aca, porque aun no estamos usando inventario
