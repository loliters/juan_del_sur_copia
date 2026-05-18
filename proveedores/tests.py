# tests.py dentro de la app 'proveedores'

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from proveedores.models import Proveedor


class ProveedoresViewsTest(TestCase):
    """Pruebas unitarias para las vistas de proveedores"""

    def setUp(self):
        # Cliente para simular peticiones
        self.client = Client()

        # URLs
        self.lista_url = reverse('proveedores:lista')
        self.crear_url = reverse('proveedores:crear')
        self.editar_url = lambda id: reverse('proveedores:editar', args=[id])
        self.eliminar_url = lambda id: reverse('proveedores:eliminar', args=[id])

        # Crear un proveedor de prueba (activo)
        self.proveedor = Proveedor.objects.create(
            nomProv='Proveedor Test',
            direccion='Calle Falsa 123',
            email='test@proveedor.com',
            telefono='123456789',
            estado=True
        )

        # Datos válidos para crear/editar
        self.datos_validos = {
            'nomProv': 'Nuevo Proveedor',
            'direccion': 'Av. Siempre Viva 742',
            'email': 'nuevo@proveedor.com',
            'telefono': '987654321'
        }

    # ==================== LISTA ====================
    def test_lista_proveedores_sin_sesion_redirige_login(self):
        """Sin sesión activa debe redirigir al login"""
        response = self.client.get(self.lista_url)
        self.assertRedirects(response, reverse('login'))

    def test_lista_proveedores_con_sesion_muestra_proveedores(self):
        """Con sesión activa muestra la lista de proveedores activos"""
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.get(self.lista_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/lista.html')
        self.assertIn('proveedores', response.context)
        self.assertEqual(list(response.context['proveedores']), [self.proveedor])

    def test_lista_proveedores_envia_roles_al_contexto(self):
        """El contexto debe contener es_cajero y es_admin según el rol de sesión"""
        # Caso administrador
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.get(self.lista_url)
        self.assertTrue(response.context['es_admin'])
        self.assertFalse(response.context['es_cajero'])

        # Caso cajero
        session['rol'] = 'cajero'
        session.save()
        response = self.client.get(self.lista_url)
        self.assertTrue(response.context['es_cajero'])
        self.assertFalse(response.context['es_admin'])

    def test_lista_proveedores_solo_muestra_activos(self):
        """Solo deben aparecer proveedores con estado=True"""
        # Crear un proveedor inactivo
        Proveedor.objects.create(
            nomProv='Inactivo',
            direccion='Inactiva 1',
            estado=False
        )
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.get(self.lista_url)
        proveedores_en_template = response.context['proveedores']
        self.assertEqual(len(proveedores_en_template), 1)
        self.assertEqual(proveedores_en_template[0].id, self.proveedor.id)

    # ==================== CREAR ====================
    def test_crear_proveedor_sin_sesion_redirige_login(self):
        response = self.client.get(self.crear_url)
        self.assertRedirects(response, reverse('login'))

    def test_crear_proveedor_cajero_acceso_denegado(self):
        """Un usuario con rol 'cajero' no puede acceder a crear"""
        session = self.client.session
        session['usuario_id'] = 2
        session['rol'] = 'cajero'
        session.save()

        response = self.client.get(self.crear_url)
        self.assertRedirects(response, self.lista_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('denegado', messages[0].message)

        # También probar POST
        response_post = self.client.post(self.crear_url, self.datos_validos)
        self.assertRedirects(response_post, self.lista_url)
        self.assertFalse(Proveedor.objects.filter(nomProv='Nuevo Proveedor').exists())

    def test_crear_proveedor_admin_get_muestra_formulario(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.get(self.crear_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/crear.html')

    def test_crear_proveedor_admin_post_valido_crea_proveedor(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.post(self.crear_url, self.datos_validos)
        self.assertRedirects(response, self.lista_url)
        self.assertTrue(Proveedor.objects.filter(nomProv='Nuevo Proveedor').exists())
        proveedor = Proveedor.objects.get(nomProv='Nuevo Proveedor')
        self.assertEqual(proveedor.direccion, 'Av. Siempre Viva 742')
        self.assertTrue(proveedor.estado)

        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('creado correctamente', messages[0].message)

    def test_crear_proveedor_admin_post_falta_nombre_o_direccion(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        # Falta nombre
        response = self.client.post(self.crear_url, {
            'direccion': 'Solo dirección',
            'email': 'test@test.com'
        })
        self.assertRedirects(response, self.crear_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Nombre y dirección son obligatorios', messages[0].message)
        self.assertFalse(Proveedor.objects.filter(direccion='Solo dirección').exists())

        # Falta dirección
        response = self.client.post(self.crear_url, {
            'nomProv': 'Sin dirección'
        })
        self.assertRedirects(response, self.crear_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Nombre y dirección son obligatorios', messages[0].message)

    def test_crear_proveedor_admin_post_direccion_duplicada(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        # Primero creamos un proveedor con una dirección
        Proveedor.objects.create(
            nomProv='Existente',
            direccion='Calle Duplicada',
            estado=True
        )

        # Intentamos crear otro con misma dirección
        response = self.client.post(self.crear_url, {
            'nomProv': 'Otro Nombre',
            'direccion': 'calle duplicada'  # case-insensitive
        })
        self.assertRedirects(response, self.crear_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Ya existe un proveedor con esa dirección', messages[0].message)
        self.assertEqual(Proveedor.objects.filter(direccion__iexact='Calle Duplicada').count(), 1)

    def test_crear_proveedor_admin_post_nombre_duplicado_muestra_warning(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        # Crear proveedor con nombre X
        Proveedor.objects.create(
            nomProv='Nombre Repetido',
            direccion='Dirección Original',
            estado=True
        )

        # Intentar crear otro con mismo nombre pero distinta dirección
        response = self.client.post(self.crear_url, {
            'nomProv': 'nombre repetido',
            'direccion': 'Otra Dirección Diferente'
        })
        self.assertRedirects(response, self.lista_url)
        # A pesar del warning, se crea el proveedor (la vista solo muestra warning, no error)
        self.assertTrue(Proveedor.objects.filter(nomProv__iexact='Nombre Repetido').count(), 2)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Ya existe un proveedor con ese nombre', messages[0].message)

    # ==================== EDITAR ====================
    def test_editar_proveedor_sin_sesion_redirige_login(self):
        response = self.client.get(self.editar_url(self.proveedor.id))
        self.assertRedirects(response, reverse('login'))

    def test_editar_proveedor_cajero_acceso_denegado(self):
        session = self.client.session
        session['usuario_id'] = 2
        session['rol'] = 'cajero'
        session.save()

        response = self.client.get(self.editar_url(self.proveedor.id))
        self.assertRedirects(response, self.lista_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('denegado', messages[0].message)

        # POST también denegado
        response_post = self.client.post(self.editar_url(self.proveedor.id), {'nomProv': 'Cambio no permitido'})
        self.assertRedirects(response_post, self.lista_url)
        self.proveedor.refresh_from_db()
        self.assertNotEqual(self.proveedor.nomProv, 'Cambio no permitido')

    def test_editar_proveedor_admin_get_muestra_formulario(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.get(self.editar_url(self.proveedor.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/editar.html')
        self.assertEqual(response.context['proveedor'].id, self.proveedor.id)

    def test_editar_proveedor_admin_post_valido_actualiza(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        nuevos_datos = {
            'nomProv': 'Proveedor Actualizado',
            'direccion': 'Nueva Dirección 456',
            'email': 'actualizado@mail.com',
            'telefono': '111222333'
        }
        response = self.client.post(self.editar_url(self.proveedor.id), nuevos_datos)
        self.assertRedirects(response, self.lista_url)
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.nomProv, 'Proveedor Actualizado')
        self.assertEqual(self.proveedor.direccion, 'Nueva Dirección 456')
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Proveedor actualizado', messages[0].message)

    def test_editar_proveedor_admin_post_nombre_vacio(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.post(self.editar_url(self.proveedor.id), {
            'nomProv': '   ',
            'direccion': 'Alguna dirección'
        })
        self.assertRedirects(response, self.editar_url(self.proveedor.id))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('El nombre es obligatorio', messages[0].message)
        self.proveedor.refresh_from_db()
        self.assertNotEqual(self.proveedor.nomProv, '')

    def test_editar_proveedor_admin_post_nombre_duplicado_otro_proveedor(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        # Crear otro proveedor
        otro = Proveedor.objects.create(
            nomProv='Otro Proveedor',
            direccion='Otra calle',
            estado=True
        )

        # Intentar cambiar el proveedor original por un nombre que ya tiene 'otro'
        response = self.client.post(self.editar_url(self.proveedor.id), {
            'nomProv': 'Otro Proveedor',  # ya existe en otro proveedor
            'direccion': 'Alguna dirección'
        })
        self.assertRedirects(response, self.editar_url(self.proveedor.id))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Ya existe ese proveedor', messages[0].message)
        self.proveedor.refresh_from_db()
        self.assertNotEqual(self.proveedor.nomProv, 'Otro Proveedor')

    # ==================== ELIMINAR (SOFT) ====================
    def test_eliminar_proveedor_sin_sesion_redirige_login(self):
        response = self.client.get(self.eliminar_url(self.proveedor.id))
        self.assertRedirects(response, reverse('login'))

    def test_eliminar_proveedor_cajero_acceso_denegado(self):
        session = self.client.session
        session['usuario_id'] = 2
        session['rol'] = 'cajero'
        session.save()

        response = self.client.get(self.eliminar_url(self.proveedor.id))
        self.assertRedirects(response, self.lista_url)

        # POST también denegado
        response_post = self.client.post(self.eliminar_url(self.proveedor.id))
        self.assertRedirects(response_post, self.lista_url)
        self.proveedor.refresh_from_db()
        self.assertTrue(self.proveedor.estado)  # sigue activo

    def test_eliminar_proveedor_admin_get_muestra_confirmacion(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.get(self.eliminar_url(self.proveedor.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proveedores/eliminar.html')
        self.assertEqual(response.context['proveedor'].id, self.proveedor.id)

    def test_eliminar_proveedor_admin_post_soft_delete(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        response = self.client.post(self.eliminar_url(self.proveedor.id))
        self.assertRedirects(response, self.lista_url)
        self.proveedor.refresh_from_db()
        self.assertFalse(self.proveedor.estado)  # ahora inactivo
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('Proveedor eliminado', messages[0].message)

    def test_eliminar_proveedor_admin_post_proveedor_no_existente_404(self):
        session = self.client.session
        session['usuario_id'] = 1
        session['rol'] = 'administrador'
        session.save()

        url_inexistente = self.editar_url(9999)  # ID que no existe
        response = self.client.get(url_inexistente)
        self.assertEqual(response.status_code, 404)

        response_post = self.client.post(url_inexistente)
        self.assertEqual(response_post.status_code, 404)