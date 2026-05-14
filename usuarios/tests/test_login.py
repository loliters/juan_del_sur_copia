import pytest
from django.contrib.auth.hashers import make_password
from usuarios.models import Usuario, Rol



#1. LOGIN ADMIN EXITOSO

@pytest.mark.django_db
def test_login_admin_exitoso(client):

    rol = Rol.objects.create(nom_rol="administrador")

    Usuario.objects.create(
        nom_usuario="Admin",
        ap1="Perez",
        email="admin@test.com",
        password=make_password("Admin123*"),
        rol=rol,
        estado=True
    )

    response = client.post('/usuarios/login/', {
        'email': 'admin@test.com',
        'password': 'Admin123*'
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/dashboard/admin/'



#2.  Login cajero exitoso

@pytest.mark.django_db
def test_login_cajero_exitoso(client):

    rol = Rol.objects.create(nom_rol="cajero")

    Usuario.objects.create(
        nom_usuario="Juan",
        ap1="Perez",
        email="juan@test.com",
        password=make_password("Juan123*"),
        rol=rol,
        estado=True
    )

    response = client.post('/usuarios/login/', {
        'email': 'juan@test.com',
        'password': 'Juan123*'
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/dashboard/cajero/'



#3. Cmpos vacios

@pytest.mark.django_db
def test_login_campos_vacios(client):

    response = client.post('/usuarios/login/', {
        'email': '',
        'password': ''
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/login/'



#4.  Email invalido

@pytest.mark.django_db
def test_login_email_invalido(client):

    response = client.post('/usuarios/login/', {
        'email': 'correo_invalido',
        'password': '123456'
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/login/'



#5 USUARIO INEXISTENTE

@pytest.mark.django_db
def test_login_usuario_inexistente(client):

    response = client.post('/usuarios/login/', {
        'email': 'noexiste@test.com',
        'password': '123456'
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/login/'



#6 PASSWORD INCORRECTA

@pytest.mark.django_db
def test_login_password_incorrecta(client):

    rol = Rol.objects.create(nom_rol="administrador")

    Usuario.objects.create(
        nom_usuario="Admin",
        ap1="Perez",
        email="admin@test.com",
        password=make_password("Correcta123*"),
        rol=rol,
        estado=True
    )

    response = client.post('/usuarios/login/', {
        'email': 'admin@test.com',
        'password': 'Incorrecta123*'
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/login/'


#7. Usuario inactivo
@pytest.mark.django_db
def test_login_usuario_deshabilitado(client):

    rol = Rol.objects.create(nom_rol="administrador")

    Usuario.objects.create(
        nom_usuario="Admin",
        ap1="Perez",
        email="admin@test.com",
        password=make_password("Admin123*"),
        rol=rol,
        estado=False
    )

    response = client.post('/usuarios/login/', {
        'email': 'admin@test.com',
        'password': 'Admin123*'
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/login/'



#8 USUARIO SIN ROL, ya no, se valida en la base de datos

#@pytest.mark.django_db
#def test_login_usuario_sin_rol(client):

#    Usuario.objects.create(
#        nom_usuario="Admin",
#        ap1="Perez",
#        email="admin@test.com",
#        password=make_password("Admin123*"),
#        rol=None,
#        estado=True
#    )

#    response = client.post('/usuarios/login/', {
#        'email': 'admin@test.com',
#        'password': 'Admin123*'
#    })

 #   assert response.status_code == 302
  #  assert response.url == '/usuarios/login/'



#9 ROL INVALIDO

@pytest.mark.django_db
def test_login_rol_invalido(client):

    rol = Rol.objects.create(nom_rol="supervisor")

    Usuario.objects.create(
        nom_usuario="Admin",
        ap1="Perez",
        email="admin@test.com",
        password=make_password("Admin123*"),
        rol=rol,
        estado=True
    )

    response = client.post('/usuarios/login/', {
        'email': 'admin@test.com',
        'password': 'Admin123*'
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/login/'



# 10 VERIFICAR SESION CREADA

@pytest.mark.django_db
def test_login_sesion_creada(client):

    rol = Rol.objects.create(nom_rol="administrador")

    usuario = Usuario.objects.create(
        nom_usuario="Admin",
        ap1="Perez",
        email="admin@test.com",
        password=make_password("Admin123*"),
        rol=rol,
        estado=True
    )

    client.post('/usuarios/login/', {
        'email': 'admin@test.com',
        'password': 'Admin123*'
    })

    session = client.session

    assert session['usuario_id'] == usuario.id
    assert session['rol'] == 'administrador'
    assert session['email'] == 'admin@test.com'



# 11 EMAIL CON MAYUSCULAS

@pytest.mark.django_db
def test_login_email_con_mayusculas(client):

    rol = Rol.objects.create(nom_rol="administrador")

    Usuario.objects.create(
        nom_usuario="Admin",
        ap1="Perez",
        email="admin@test.com",
        password=make_password("Admin123*"),
        rol=rol,
        estado=True
    )

    response = client.post('/usuarios/login/', {
        'email': 'ADMIN@TEST.COM',
        'password': 'Admin123*'
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/dashboard/admin/'



#12. PASSWORD CON ESPACIOS

@pytest.mark.django_db
def test_login_password_con_espacios(client):

    rol = Rol.objects.create(nom_rol="administrador")

    Usuario.objects.create(
        nom_usuario="Admin",
        ap1="Perez",
        email="admin@test.com",
        password=make_password("Admin123*"),
        rol=rol,
        estado=True
    )

    response = client.post('/usuarios/login/', {
        'email': 'admin@test.com',
        'password': ' Admin123* '
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/login/'



#13. SQL INJECTION

@pytest.mark.django_db
def test_login_sql_injection(client):

    response = client.post('/usuarios/login/', {
        'email': "' OR '1'='1",
        'password': "' OR '1'='1"
    })

    assert response.status_code == 302
    assert response.url == '/usuarios/login/'