import pytest
from clientes.models import Cliente

# =========================================
# FIXTURE PARA LIMPIAR BASE DE DATOS ANTES DE CADA TEST
# =========================================
@pytest.fixture(autouse=True)
def limpiar_clientes(db):
    """Elimina todos los clientes antes de cada test"""
    Cliente.objects.all().delete()
    yield

# clientes/tests/test_clientes.py

import pytest
from clientes.models import Cliente


# =========================================
# 1. REGISTRO CLIENTE EXITOSO
# =========================================
@pytest.mark.django_db
def test_registro_cliente_exitoso(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    response = client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert response.status_code == 200
    assert Cliente.objects.count() == 1


# =========================================
# 2. NOMBRE VACÍO
# =========================================
@pytest.mark.django_db
def test_nombre_vacio(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': '',
        'email': 'juan@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 3. NOMBRE CON NÚMEROS
# =========================================
@pytest.mark.django_db
def test_nombre_con_numeros(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan123',
        'email': 'juan@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 4. RAZÓN SOCIAL CON NÚMEROS
# =========================================
@pytest.mark.django_db
def test_razon_social_con_numeros(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'razonSocial': 'Empresa123',
        'email': 'juan@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 5. CARNET CON LETRAS
# =========================================
@pytest.mark.django_db
def test_carnet_con_letras(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'carnet': 'ABC123',
        'email': 'juan@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 6. CARNET REPETIDO
# =========================================
@pytest.mark.django_db
def test_carnet_repetido(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    Cliente.objects.create(
        nombre='Pedro',
        carnet='123456',
        email='pedro@test.com',
        telefono='70000000'
    )

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'carnet': '123456',
        'email': 'juan@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 1


# =========================================
# 7. EMAIL VACÍO
# =========================================
@pytest.mark.django_db
def test_email_vacio(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': '',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 8. EMAIL INVÁLIDO
# =========================================
@pytest.mark.django_db
def test_email_invalido(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 9. EMAIL REPETIDO
# =========================================
@pytest.mark.django_db
def test_email_repetido(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    Cliente.objects.create(
        nombre='Pedro',
        email='juan@test.com',
        telefono='70000000'
    )

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 1


# =========================================
# 10. TELÉFONO VACÍO
# =========================================
@pytest.mark.django_db
def test_telefono_vacio(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': ''
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 11. TELÉFONO CON LETRAS
# =========================================
@pytest.mark.django_db
def test_telefono_con_letras(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '77ABC'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 12. TELÉFONO REPETIDO
# =========================================
@pytest.mark.django_db
def test_telefono_repetido(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    Cliente.objects.create(
        nombre='Pedro',
        email='pedro@test.com',
        telefono='77777777'
    )

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 1


# =========================================
# 13. ZONA CON NÚMEROS
# =========================================
@pytest.mark.django_db
def test_zona_con_numeros(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '77777777',
        'zona': 'Zona123'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 14. CALLE CON CARACTERES ESPECIALES
# =========================================
@pytest.mark.django_db
def test_calle_caracteres_especiales(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '77777777',
        'calle': '@@@@'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 15. NÚMERO CASA CON LETRAS
# =========================================
@pytest.mark.django_db
def test_numero_casa_con_letras(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '77777777',
        'numeroCasa': '12A'
    }, follow=True)

    assert Cliente.objects.count() == 0


# =========================================
# 16. REGISTRO SIN LOGIN
# =========================================
@pytest.mark.django_db
def test_registro_cliente_sin_login(client):

    response = client.post('/clientes/registro/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '77777777'
    })

    assert response.status_code == 302


# =========================================
# 17. VER CLIENTES SIN LOGIN
# =========================================
@pytest.mark.django_db
def test_ver_clientes_sin_login(client):

    response = client.get('/clientes/ver/')

    assert response.status_code == 302


# =========================================
# 18. EDITAR CLIENTE EXITOSO
# =========================================
@pytest.mark.django_db
def test_editar_cliente_exitoso(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    cliente = Cliente.objects.create(
        nombre='Juan',
        email='juan@test.com',
        telefono='77777777'
    )

    response = client.post(f'/clientes/editar/{cliente.id_cliente}/', {
        'nombre': 'Pedro',
        'email': 'pedro@test.com',
        'telefono': '70000000'
    }, follow=True)

    cliente.refresh_from_db()

    assert response.status_code == 200
    assert cliente.nombre == 'Pedro'


# =========================================
# 19. EDITAR EMAIL REPETIDO
# =========================================
@pytest.mark.django_db
def test_editar_email_repetido(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    Cliente.objects.create(
        nombre='Pedro',
        email='pedro@test.com',
        telefono='70000000'
    )

    cliente2 = Cliente.objects.create(
        nombre='Juan',
        email='juan@test.com',
        telefono='77777777'
    )

    client.post(f'/clientes/editar/{cliente2.id_cliente}/', {
        'nombre': 'Juan',
        'email': 'pedro@test.com',
        'telefono': '77777777'
    }, follow=True)

    cliente2.refresh_from_db()

    assert cliente2.email == 'juan@test.com'


# =========================================
# 20. EDITAR TELÉFONO REPETIDO
# =========================================
@pytest.mark.django_db
def test_editar_telefono_repetido(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    Cliente.objects.create(
        nombre='Pedro',
        email='pedro@test.com',
        telefono='70000000'
    )

    cliente2 = Cliente.objects.create(
        nombre='Juan',
        email='juan@test.com',
        telefono='77777777'
    )

    client.post(f'/clientes/editar/{cliente2.id_cliente}/', {
        'nombre': 'Juan',
        'email': 'juan@test.com',
        'telefono': '70000000'
    }, follow=True)

    cliente2.refresh_from_db()

    assert cliente2.telefono == '77777777'


# =========================================
# 21. ELIMINAR CLIENTE
# =========================================
@pytest.mark.django_db
def test_eliminar_cliente(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    cliente = Cliente.objects.create(
        nombre='Juan',
        email='juan@test.com',
        telefono='77777777',
        estado=True
    )

    response = client.post(
        f'/clientes/eliminar/{cliente.id_cliente}/',
        follow=True
    )

    cliente.refresh_from_db()

    assert response.status_code == 200
    assert cliente.estado is False


# =========================================
# 22. RESTAURAR CLIENTE
# =========================================
@pytest.mark.django_db
def test_restaurar_cliente(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    cliente = Cliente.objects.create(
        nombre='Juan',
        email='juan@test.com',
        telefono='77777777',
        estado=False
    )

    response = client.get(
        f'/clientes/restaurar/{cliente.id_cliente}/',
        follow=True
    )

    cliente.refresh_from_db()

    assert response.status_code == 200
    assert cliente.estado is True


# =========================================
# 23. VER CLIENTES INACTIVOS
# =========================================
@pytest.mark.django_db
def test_ver_clientes_inactivos(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    Cliente.objects.create(
        nombre='Juan',
        email='juan@test.com',
        telefono='77777777',
        estado=False
    )

    response = client.get('/clientes/inactivos/')

    assert response.status_code == 200


# =========================================
# 24. SQL INJECTION
# =========================================
@pytest.mark.django_db
def test_sql_injection_cliente(client):

    session = client.session
    session['usuario_id'] = 1
    session.save()

    client.post('/clientes/registro/', {
        'nombre': "' OR 1=1 --",
        'email': 'hack@test.com',
        'telefono': '77777777'
    }, follow=True)

    assert Cliente.objects.count() == 0