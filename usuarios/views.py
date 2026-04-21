from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError

from .models import Usuario, Rol


# =========================
# LOGIN
# =========================
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import Usuario
import re


def login_view(request):

    if request.method == "POST":

        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # ==========================================
        # VALIDACIÓN 1: Campos vacíos
        # ==========================================
        if not email or not password:
            messages.error(request, '⚠️ Completa todos los campos')
            return redirect('login')

        # ==========================================
        # VALIDACIÓN 2: Formato de email
        # ==========================================
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, '❌ Correo electrónico inválido')
            return redirect('login')

        # ==========================================
        # VALIDACIÓN 3: Buscar usuario
        # ==========================================
        try:
            user = Usuario.objects.select_related('rol').get(email__iexact=email)
        except Usuario.DoesNotExist:
            # Mensaje genérico por seguridad (no especifica si es email o contraseña)
            messages.error(request, '❌ Usuario o contraseña incorrectos')
            return redirect('login')

        # ==========================================
        # VALIDACIÓN 4: Usuario activo
        # ==========================================
        if not user.estado:
            messages.error(request, '🚫 Usuario deshabilitado. Contacta al administrador')
            return redirect('login')

        # ==========================================
        # VALIDACIÓN 5: Contraseña incorrecta
        # ==========================================
        if not check_password(password, user.password):
            messages.error(request, '❌ Usuario o contraseña incorrectos')
            return redirect('login')

        # ==========================================
        # VALIDACIÓN 6: Rol asignado
        # ==========================================
        if not user.rol or not user.rol.nom_rol:
            messages.error(request, '⚠️ Usuario sin rol asignado. Contacta al administrador')
            return redirect('login')

        # ==========================================
        # INICIAR SESIÓN
        # ==========================================
        rol = user.rol.nom_rol.strip().lower()

        # Guardar sesión
        request.session['usuario_id'] = user.id
        request.session['rol'] = rol
        request.session['nombre'] = user.nom_usuario
        request.session['email'] = user.email

        # Mensaje de bienvenida
        messages.success(request, f'✅ ¡Bienvenido {user.nom_usuario}!')

        # Redirección por rol
        if rol == "administrador":
            return redirect('dashboard_admin')
        elif rol == "cajero":
            return redirect('dashboard_cajero')
        else:
            messages.error(request, '❌ Rol no válido en el sistema')
            return redirect('login')

    return render(request, 'usuarios/login.html')

# =========================
# REGISTER
# =========================

from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse
from .models import Usuario, Rol
import re


def register(request):

    roles = Rol.objects.all()

    if request.method == "POST":

        nom_usuario = request.POST.get('nom_usuario', '').strip()
        ap1 = request.POST.get('ap1', '').strip()
        ap2 = request.POST.get('ap2', '').strip()
        password = request.POST.get('password', '')
        rol_id = request.POST.get('rol')
        estado = request.POST.get('estado') == 'on'

        # ==========================================
        # VALIDACIÓN 1: Al menos nombre o un apellido
        # ==========================================
        if not nom_usuario and not ap1 and not ap2:
            messages.error(request, 'Debes ingresar al menos un nombre o apellido')
            return redirect('register')

        # ==========================================
        # VALIDACIÓN 2: Solo letras (sin números)
        # ==========================================
        pattern_letters = r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$'
        
        if nom_usuario:
            if not re.match(pattern_letters, nom_usuario):
                messages.error(request, 'El nombre solo debe contener letras (sin números)')
                return redirect('register')
            if len(nom_usuario.strip()) == 0:
                messages.error(request, 'El nombre no puede estar vacío')
                return redirect('register')
        
        if ap1:
            if not re.match(pattern_letters, ap1):
                messages.error(request, 'El primer apellido solo debe contener letras (sin números)')
                return redirect('register')
        
        if ap2:
            if not re.match(pattern_letters, ap2):
                messages.error(request, 'El segundo apellido solo debe contener letras (sin números)')
                return redirect('register')

        # ==========================================
        # VALIDACIÓN 3: Campos obligatorios
        # ==========================================
        if not password or not rol_id:
            messages.error(request, 'Completa todos los campos obligatorios')
            return redirect('register')

        # ==========================================
        # VALIDACIÓN 4: Contraseña fuerte
        # ==========================================
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&._-])[A-Za-z\d@$!%*#?&._-]{8,}$', password):
            messages.error(request, 'La contraseña debe tener mínimo 8 caracteres, letras, números y un símbolo')
            return redirect('register')

        # ==========================================
        # VALIDACIÓN 5: Rol existe
        # ==========================================
        try:
            rol_obj = Rol.objects.get(id=rol_id)
        except Rol.DoesNotExist:
            messages.error(request, 'Rol inválido')
            return redirect('register')

        # ==========================================
        # GENERAR EMAIL (lógica corregida)
        # ==========================================
        # Construir la base del email
        partes = []
        
        # Agregar nombre si existe
        if nom_usuario:
            nombre_limpio = re.sub(r'\s+', ' ', nom_usuario).strip()
            primer_nombre = nombre_limpio.split()[0].lower()
            partes.append(primer_nombre)
        
        # Lógica CORREGIDA para apellidos:
        # - Si tiene primer apellido, usar ese
        # - Si NO tiene primer apellido PERO SÍ tiene segundo apellido, usar el segundo
        # - Si tiene ambos, usar el primero
        if ap1:  # Prioridad al primer apellido
            apellido_limpio = re.sub(r'\s+', ' ', ap1).strip()
            primer_apellido = apellido_limpio.split()[0].lower()
            partes.append(primer_apellido)
        elif ap2:  # Solo si NO hay primer apellido, usar el segundo
            apellido_limpio = re.sub(r'\s+', ' ', ap2).strip()
            segundo_apellido = apellido_limpio.split()[0].lower()
            partes.append(segundo_apellido)
        
        # Unir con punto
        base = '.'.join(partes) if partes else 'usuario'
        
        # Dominio fijo
        dominio = "juandelsur.com"
        
        # ==========================================
        # VALIDACIÓN 6: Evitar duplicados de email
        # ==========================================
        email_final = f"{base}@{dominio}"
        contador = 1
        
        # Buscar si ya existe el email
        while Usuario.objects.filter(email=email_final).exists():
            contador += 1
            email_final = f"{base}{contador}@{dominio}"
        
        # ==========================================
        # VALIDACIONES ADICIONALES
        # ==========================================
        
        # 7. Validar que el nombre/apellido no sea muy largo
        if nom_usuario and len(nom_usuario) > 100:
            messages.error(request, 'El nombre es demasiado largo (máximo 100 caracteres)')
            return redirect('register')
        
        if ap1 and len(ap1) > 100:
            messages.error(request, 'El primer apellido es demasiado largo (máximo 100 caracteres)')
            return redirect('register')
        
        if ap2 and len(ap2) > 100:
            messages.error(request, 'El segundo apellido es demasiado largo (máximo 100 caracteres)')
            return redirect('register')
        
        # 8. Validar que la contraseña no sea demasiado larga
        if len(password) > 128:
            messages.error(request, 'La contraseña es demasiado larga (máximo 128 caracteres)')
            return redirect('register')
        
        # 9. Validar caracteres especiales no permitidos en nombre/apellidos
        caracteres_especiales = r'[!@#$%^&*()_+=\[\]{};:""\\|,.<>/?]'
        if nom_usuario and re.search(caracteres_especiales, nom_usuario):
            messages.error(request, 'El nombre no debe contener caracteres especiales')
            return redirect('register')
        
        if ap1 and re.search(caracteres_especiales, ap1):
            messages.error(request, 'El primer apellido no debe contener caracteres especiales')
            return redirect('register')
        
        if ap2 and re.search(caracteres_especiales, ap2):
            messages.error(request, 'El segundo apellido no debe contener caracteres especiales')
            return redirect('register')
        
        # 10. Validar que el email generado no sea demasiado largo
        if len(email_final) > 254:
            messages.error(request, 'El email generado es demasiado largo')
            return redirect('register')

        # ==========================================
        # GUARDAR USUARIO
        # ==========================================
        try:
            Usuario.objects.create(
                nom_usuario=nom_usuario,
                ap1=ap1,
                ap2=ap2,
                email=email_final,
                password=make_password(password),
                rol=rol_obj,
                estado=estado
            )

        except IntegrityError as e:
            messages.error(request, f'Error al registrar usuario: {str(e)}')
            return redirect('register')

        messages.success(request, f'Usuario creado correctamente. Email: {email_final}')
        return redirect('login')

    # GET (form vacío)
    return render(request, 'usuarios/register.html', {
        'roles': roles
    })


# ==========================================
# VISTA PARA GENERAR EMAIL EN TIEMPO REAL (AJAX)
# ==========================================
def generar_email_preview(request):
    """
    Vista AJAX que genera el email en tiempo real mientras el usuario escribe
    """
    if request.method == "GET" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        nom_usuario = request.GET.get('nom_usuario', '').strip()
        ap1 = request.GET.get('ap1', '').strip()
        ap2 = request.GET.get('ap2', '').strip()
        
        # Generar email con la misma lógica que en register
        partes = []
        
        if nom_usuario:
            nombre_limpio = re.sub(r'\s+', ' ', nom_usuario).strip()
            primer_nombre = nombre_limpio.split()[0].lower()
            partes.append(primer_nombre)
        
        if ap1:
            apellido_limpio = re.sub(r'\s+', ' ', ap1).strip()
            primer_apellido = apellido_limpio.split()[0].lower()
            partes.append(primer_apellido)
        elif ap2:
            apellido_limpio = re.sub(r'\s+', ' ', ap2).strip()
            segundo_apellido = apellido_limpio.split()[0].lower()
            partes.append(segundo_apellido)
        
        base = '.'.join(partes) if partes else 'usuario'
        dominio = "juandelsur.com"
        
        email_generado = f"{base}@{dominio}"
        
        # Verificar si el email ya existe (para mostrar preview con posible número)
        email_final = email_generado
        contador = 1
        while Usuario.objects.filter(email=email_final).exists():
            contador += 1
            email_final = f"{base}{contador}@{dominio}"
        
        return JsonResponse({
            'success': True,
            'email': email_final,
            'base_email': email_generado
        })
    
    return JsonResponse({'success': False, 'error': 'Solicitud inválida'})
# =========================
# DASHBOARD CAJERO
# =========================
def dashboard_cajero(request):

    if request.session.get('usuario_id') is None:
        return redirect('login')

    return render(request, 'usuarios/dashboard_cajero.html')


# =========================
# DASHBOARD ADMIN
# =========================
def dashboard_admin(request):

    if request.session.get('rol') != "administrador":
        return redirect('login')

    usuarios = Usuario.objects.select_related('rol').all().filter(estado=True)

    return render(request, 'usuarios/dashboard_admin.html', {
        'usuarios': usuarios
    })


# =========================
# MODIFICAR USUARIO
# =========================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Usuario, Rol
import re


def modify(request, id):

    usuario_sesion = request.session.get('usuario_id')
    rol_sesion = (request.session.get('rol') or '').strip().lower()

    if not usuario_sesion:
        return redirect('login')

    if rol_sesion != "administrador":
        return redirect('login')

    usuario = get_object_or_404(Usuario, id=id)
    roles = Rol.objects.all()

    if request.method == "POST":

        # ==========================================
        # OBTENER DATOS DEL FORMULARIO
        # ==========================================
        nom_usuario = request.POST.get('nom_usuario', '').strip()
        ap1 = request.POST.get('ap1', '').strip()
        ap2 = request.POST.get('ap2', '').strip()
        email = request.POST.get('email', '').strip()
        estado = request.POST.get('estado') == 'on'
        rol_id = request.POST.get('rol')

        # Al menos nombre o un apellido
        if not nom_usuario and not ap1 and not ap2:
            messages.error(request, 'Debes ingresar al menos un nombre o apellido')
            return redirect('modify', id=id)

        # Solo letras (sin números)
        pattern_letters = r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$'
        
        if nom_usuario:
            if not re.match(pattern_letters, nom_usuario):
                messages.error(request, 'El nombre solo debe contener letras (sin números)')
                return redirect('modify', id=id)
            if len(nom_usuario.strip()) == 0:
                messages.error(request, 'El nombre no puede estar vacío')
                return redirect('modify', id=id)
        
        if ap1:
            if not re.match(pattern_letters, ap1):
                messages.error(request, 'El primer apellido solo debe contener letras (sin números)')
                return redirect('modify', id=id)
        
        if ap2:
            if not re.match(pattern_letters, ap2):
                messages.error(request, 'El segundo apellido solo debe contener letras (sin números)')
                return redirect('modify', id=id)

        # Rol existe
        if not rol_id:
            messages.error(request, 'Debes seleccionar un rol')
            return redirect('modify', id=id)
            
        try:
            rol_obj = Rol.objects.get(id=rol_id)
        except Rol.DoesNotExist:
            messages.error(request, 'Rol inválido')
            return redirect('modify', id=id)

        # Caracteres especiales no permitidos
        caracteres_especiales = r'[!@#$%^&*()_+=\[\]{};:""\\|,.<>/?]'
        if nom_usuario and re.search(caracteres_especiales, nom_usuario):
            messages.error(request, 'El nombre no debe contener caracteres especiales')
            return redirect('modify', id=id)
        
        if ap1 and re.search(caracteres_especiales, ap1):
            messages.error(request, 'El primer apellido no debe contener caracteres especiales')
            return redirect('modify', id=id)
        
        if ap2 and re.search(caracteres_especiales, ap2):
            messages.error(request, 'El segundo apellido no debe contener caracteres especiales')
            return redirect('modify', id=id)

        # Longitud máxima
        if nom_usuario and len(nom_usuario) > 100:
            messages.error(request, 'El nombre es demasiado largo (máximo 100 caracteres)')
            return redirect('modify', id=id)
        
        if ap1 and len(ap1) > 100:
            messages.error(request, 'El primer apellido es demasiado largo (máximo 100 caracteres)')
            return redirect('modify', id=id)
        
        if ap2 and len(ap2) > 100:
            messages.error(request, 'El segundo apellido es demasiado largo (máximo 100 caracteres)')
            return redirect('modify', id=id)

        # Verificar que el email no sea usado por OTRO usuario
        if email:
            # Verificar si el email ya existe en otro usuario (diferente al que estamos editando)
            email_existente = Usuario.objects.filter(email=email).exclude(id=usuario.id).exists()
            if email_existente:
                messages.error(request, f'El correo {email} ya está en uso por otro usuario')
                return redirect('modify', id=id)
            
            # Validar formato de email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                messages.error(request, 'Formato de correo electrónico inválido')
                return redirect('modify', id=id)
        
        # Generar email si no viene del formulario
        # Si el email no viene del formulario o está vacío, generarlo automáticamente
        if not email:
            # Generar email con la misma lógica que en register
            partes = []
            
            if nom_usuario:
                nombre_limpio = re.sub(r'\s+', ' ', nom_usuario).strip()
                primer_nombre = nombre_limpio.split()[0].lower()
                partes.append(primer_nombre)
            
            if ap1:
                apellido_limpio = re.sub(r'\s+', ' ', ap1).strip()
                primer_apellido = apellido_limpio.split()[0].lower()
                partes.append(primer_apellido)
            elif ap2:
                apellido_limpio = re.sub(r'\s+', ' ', ap2).strip()
                segundo_apellido = apellido_limpio.split()[0].lower()
                partes.append(segundo_apellido)
            
            base = '.'.join(partes) if partes else 'usuario'
            dominio = "juandelsur.com"
            
            email_generado = f"{base}@{dominio}"
            email_final = email_generado
            contador = 1
            
            # Buscar si ya existe el email (excluyendo al usuario actual)
            while Usuario.objects.filter(email=email_final).exclude(id=usuario.id).exists():
                contador += 1
                email_final = f"{base}{contador}@{dominio}"
            
            email = email_final

        # Email no muy largo
        if len(email) > 254:
            messages.error(request, 'El email es demasiado largo')
            return redirect('modify', id=id)

        # ==========================================
        # ACTUALIZAR USUARIO
        # ==========================================
        try:
            usuario.nom_usuario = nom_usuario
            usuario.ap1 = ap1
            usuario.ap2 = ap2
            usuario.email = email
            usuario.estado = estado
            usuario.rol = rol_obj
            
            usuario.save()
            
            messages.success(request, f'✅ Usuario actualizado correctamente. Nuevo email: {email}')
            
        except IntegrityError as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
            return redirect('modify', id=id)
        
        return redirect('dashboard_admin')

    return render(request, 'usuarios/modify.html', {
        'usuario': usuario,
        'roles': roles
    })
# =========================
# LOGOUT
# =========================
def logout_view(request):

    request.session.flush()
    return redirect('login')
#==========================
#eliminar
#==========================
def eliminar_usuario(request, id):
    # Verificar que el usuario sea administrador
    if request.session.get('rol') != "administrador":
        return redirect('login')
    
    # Obtener el usuario
    usuario = Usuario.objects.get(id=id)
    
    # Cambiar el estado a False (inactivo) en lugar de eliminar
    usuario.estado = False
    usuario.save()
    
    
    return redirect('dashboard_admin')

#inactivos
from django.shortcuts import render, get_object_or_404, redirect
from .models import Usuario


def ver_inactivos(request):

    #  si hacen click en activar/desactivar
    if request.method == "POST":
        usuario_id = request.POST.get("id")
        usuario = get_object_or_404(Usuario, id=usuario_id)

        usuario.estado = not usuario.estado
        usuario.save()

        return redirect('ver_inactivos')

    #  solo inactivos
    usuarios_inactivos = Usuario.objects.filter(estado=False)

    return render(request, "usuarios/ver_inactivos.html", {
        "usuarios_inactivos": usuarios_inactivos
    })