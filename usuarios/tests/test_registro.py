#1. usuario creado
import pytest
from usuarios.models import Usuario, Rol


@pytest.mark.django_db
def test_registro_exitoso(client):

    rol = Rol.objects.create(nom_rol="cajero")

    response = client.post('/usuarios/register/', {
        'nom_usuario': 'Juan',
        'ap1': 'Perez',
        'ap2': 'Lopez',
        'password': 'Juan123*',
        'rol': rol.id,
        'estado': 'on'
    })

    usuario = Usuario.objects.first()

    assert response.status_code == 302
    assert usuario is not None

#2. contraseña hasheada
@pytest.mark.django_db
def test_password_hasheada(client):

    rol = Rol.objects.create(nom_rol="cajero")

    client.post('/usuarios/register/', {
        'nom_usuario': 'Juan',
        'ap1': 'Perez',
        'password': 'Juan123*',
        'rol': rol.id,
        'estado': 'on'
    })

    usuario = Usuario.objects.first()

    assert usuario.password != 'Juan123*'

#3. generar correo automatico
@pytest.mark.django_db
def test_generacion_email(client):

    rol = Rol.objects.create(nom_rol="cajero")

    client.post('/usuarios/register/', {
        'nom_usuario': 'Juan',
        'ap1': 'Perez',
        'password': 'Juan123*',
        'rol': rol.id,
        'estado': 'on'
    })

    usuario = Usuario.objects.first()

    assert usuario.email == 'juan.perez@juandelsur.com'

#4. correos repetidos
@pytest.mark.django_db
def test_email_repetido(client):

    rol = Rol.objects.create(nom_rol="cajero")

    client.post('/usuarios/register/', {
        'nom_usuario': 'Juan',
        'ap1': 'Perez',
        'password': 'Juan123*',
        'rol': rol.id,
        'estado': 'on'
    })

    client.post('/usuarios/register/', {
        'nom_usuario': 'Juan',
        'ap1': 'Perez',
        'password': 'Juan123*',
        'rol': rol.id,
        'estado': 'on'
    })

    usuarios = Usuario.objects.all()

    assert usuarios[0].email == 'juan.perez@juandelsur.com'
    assert usuarios[1].email == 'juan.perez2@juandelsur.com'

#5. contraseña corta
@pytest.mark.django_db
def test_password_corta(client):

    rol = Rol.objects.create(nom_rol="cajero")

    response = client.post('/usuarios/register/', {
        'nom_usuario': 'Juan',
        'ap1': 'Perez',
        'password': '123',
        'rol': rol.id,
        'estado': 'on'
    })

    usuarios = Usuario.objects.count()

    assert usuarios == 0
#6. no permitir campos vacios
@pytest.mark.django_db
def test_campos_vacios(client):

    rol = Rol.objects.create(nom_rol="cajero")

    client.post('/usuarios/register/', {
        'nom_usuario': '',
        'ap1': '',
        'ap2': '',
        'password': 'Juan123*',
        'rol': rol.id,
        'estado': 'on'
    })

    usuarios = Usuario.objects.count()

    assert usuarios == 0

#7. nombre con números
@pytest.mark.django_db
def test_nombre_con_numeros(client):

    rol = Rol.objects.create(nom_rol="cajero")

    client.post('/usuarios/register/', {
        'nom_usuario': 'Juan123',
        'ap1': 'Perez',
        'password': 'Juan123*',
        'rol': rol.id,
        'estado': 'on'
    })

    usuarios = Usuario.objects.count()

    assert usuarios == 0

#8. rol valido
@pytest.mark.django_db
def test_rol_invalido(client):

    client.post('/usuarios/register/', {
        'nom_usuario': 'Juan',
        'ap1': 'Perez',
        'password': 'Juan123*',
        'rol': 999,
        'estado': 'on'
    })

    usuarios = Usuario.objects.count()

    assert usuarios == 0

#9. nombre demasiado largo
@pytest.mark.django_db
def test_nombre_demasiado_largo(client):

    rol = Rol.objects.create(nom_rol="cajero")

    nombre_largo = "J" * 101

    client.post('/usuarios/register/', {
        'nom_usuario': nombre_largo,
        'ap1': 'Perez',
        'password': 'Juan123*',
        'rol': rol.id,
        'estado': 'on'
    })

    usuarios = Usuario.objects.count()

    assert usuarios == 0
