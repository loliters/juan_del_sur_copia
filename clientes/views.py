# clientes/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Cliente
import re

def registro_cliente(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.POST.get('nombre', '').strip()
        razonSocial = request.POST.get('razonSocial', '').strip()
        carnet = request.POST.get('carnet', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        zona = request.POST.get('zona', '').strip()
        calle = request.POST.get('calle', '').strip()
        numeroCasa = request.POST.get('numeroCasa', '').strip()
        
        # ===== VALIDACIONES =====
        errores = False
        
        # 1. Validar NOMBRE (solo letras y espacios, OBLIGATORIO)
        if not nombre:
            messages.error(request, 'El nombre es obligatorio')
            errores = True
        elif not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+$', nombre):
            messages.error(request, '❌ El nombre solo debe contener letras y espacios (sin números)')
            errores = True
        
        # 2. Validar RAZÓN SOCIAL (solo letras y espacios, OPCIONAL)
        if razonSocial and not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+$', razonSocial):
            messages.error(request, '❌ La razón social solo debe contener letras y espacios (sin números)')
            errores = True
        
        # 3. Validar CARNET (solo números, OPCIONAL)
        if carnet and not re.match(r'^[0-9]+$', carnet):
            messages.error(request, ' El carnet solo debe contener números')
            errores = True
        
        # 4. Validar EMAIL (formato válido, OBLIGATORIO)
        if not email:
            messages.error(request, 'El email es obligatorio')
            errores = True
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, 'Ingrese un correo electrónico válido')
            errores = True
        else:
            # Verificar si el email ya existe
            if Cliente.objects.filter(email=email).exists():
                messages.error(request, f'El correo electrónico "{email}" ya está registrado por otro cliente')
                errores = True
        
        # 5. Validar TELÉFONO (solo números, OBLIGATORIO)
        if not telefono:
            messages.error(request, 'El teléfono es obligatorio')
            errores = True
        elif not re.match(r'^[0-9]+$', telefono):
            messages.error(request, ' El teléfono solo debe contener números (sin letras ni guiones)')
            errores = True
        else:
            # Verificar si el teléfono ya existe
            if Cliente.objects.filter(telefono=telefono).exists():
                messages.error(request, f' El número de teléfono "{telefono}" ya está registrado por otro cliente')
                errores = True
        
        # 6. Validar ZONA (solo letras, OPCIONAL)
        if zona and not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+$', zona):
            messages.error(request, ' La zona solo debe contener letras y espacios')
            errores = True
        
        # 7. Validar CALLE (letras y números, OPCIONAL)
        if calle and not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9\s]+$', calle):
            messages.error(request, ' La calle solo debe contener letras, números y espacios')
            errores = True
        
        # 8. Validar NÚMERO DE CASA (solo números, OPCIONAL)
        if numeroCasa and not re.match(r'^[0-9]+$', numeroCasa):
            messages.error(request, ' El número de casa solo debe contener números')
            errores = True
        
        # Si hay errores, redirigir al formulario
        if errores:
            return redirect('clientes:registro_cliente')  # ← CORREGIDO con namespace
        
        # ===== CREAR CLIENTE =====
        try:
            # Obtener un método de pago por defecto
            metodo_pago_default = MetodoPago.objects.first()
            
            cliente = Cliente.objects.create(
                nombre=nombre,
                razonSocial=razonSocial if razonSocial else '',
                email=email,
                telefono=telefono,
                zona=zona if zona else '',
                calle=calle if calle else '',
                numeroCasa=numeroCasa if numeroCasa else '',
                estado=True,
                metodo_pago=metodo_pago_default
            )
            
            messages.success(request, f'¡Cliente {nombre} registrado exitosamente!')
            return redirect('clientes:lista_clientes')  # ← CORREGIDO con namespace
            
        except Exception as e:
            messages.error(request, f' Error al registrar cliente: {str(e)}')
            return redirect('clientes:registro_cliente')  # ← CORREGIDO con namespace
    
    return render(request, 'clientes/registro_cliente.html')


def ver_clientes(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    clientes = Cliente.objects.filter(estado=True).order_by('-id_cliente')
    return render(request, 'clientes/ver_clientes.html', {'clientes': clientes})

def editar_cliente(request, id):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Obtener el cliente por ID
    cliente = get_object_or_404(Cliente, id_cliente=id)
    
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.POST.get('nombre', '').strip()
        razonSocial = request.POST.get('razonSocial', '').strip()
        carnet = request.POST.get('carnet', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        zona = request.POST.get('zona', '').strip()
        calle = request.POST.get('calle', '').strip()
        numeroCasa = request.POST.get('numeroCasa', '').strip()
        
        # ===== VALIDACIONES =====
        errores = False
        
        # Validar NOMBRE
        if not nombre:
            messages.error(request, 'El nombre es obligatorio')
            errores = True
        elif not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+$', nombre):
            messages.error(request, '❌ El nombre solo debe contener letras y espacios')
            errores = True
        
        # Validar RAZÓN SOCIAL
        if razonSocial and not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+$', razonSocial):
            messages.error(request, '❌ La razón social solo debe contener letras y espacios')
            errores = True
        
        # Validar CARNET
        if carnet and not re.match(r'^[0-9]+$', carnet):
            messages.error(request, '❌ El carnet solo debe contener números')
            errores = True
        
        # Validar EMAIL
        if not email:
            messages.error(request, 'El email es obligatorio')
            errores = True
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, '❌ Ingrese un correo electrónico válido')
            errores = True
        else:
            # Verificar email no exista en otro cliente
            if Cliente.objects.filter(email=email).exclude(id_cliente=id).exists():
                messages.error(request, '❌ Este correo electrónico ya está registrado por otro cliente')
                errores = True
        
        # Validar TELÉFONO
        if not telefono:
            messages.error(request, 'El teléfono es obligatorio')
            errores = True
        elif not re.match(r'^[0-9]+$', telefono):
            messages.error(request, '❌ El teléfono solo debe contener números')
            errores = True
        else:
            # Verificar teléfono no exista en otro cliente
            if Cliente.objects.filter(telefono=telefono).exclude(id_cliente=id).exists():
                messages.error(request, '❌ Este número de teléfono ya está registrado por otro cliente')
                errores = True
        
        # Validar ZONA
        if zona and not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+$', zona):
            messages.error(request, '❌ La zona solo debe contener letras y espacios')
            errores = True
        
        # Validar CALLE
        if calle and not re.match(r'^[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9\s]+$', calle):
            messages.error(request, '❌ La calle solo debe contener letras, números y espacios')
            errores = True
        
        # Validar NÚMERO DE CASA
        if numeroCasa and not re.match(r'^[0-9]+$', numeroCasa):
            messages.error(request, '❌ El número de casa solo debe contener números')
            errores = True
        
        if errores:
            return render(request, 'clientes/editar_cliente.html', {'cliente': cliente})
        
        # Actualizar cliente
        cliente.nombre = nombre
        cliente.razonSocial = razonSocial
        cliente.carnet = carnet
        cliente.email = email
        cliente.telefono = telefono
        cliente.zona = zona
        cliente.calle = calle
        cliente.numeroCasa = numeroCasa
        cliente.save()
        
        messages.success(request, f' Cliente {nombre} actualizado exitosamente')
        return redirect('clientes:lista_clientes')
    
    return render(request, 'clientes/editar_cliente.html', {'cliente': cliente})


def eliminar_cliente(request, id):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Obtener el cliente por ID (borrado lógico - solo cambia estado)
    cliente = get_object_or_404(Cliente, id_cliente=id, estado=True)
    
    if request.method == "POST":
        nombre = cliente.nombre
        cliente.estado = False  # Borrado lógico
        cliente.save()
        messages.success(request, f'✅ Cliente "{nombre}" eliminado exitosamente')
        return redirect('clientes:lista_clientes')
    
    return render(request, 'clientes/eliminar_cliente.html', {'cliente': cliente})


def clientes_inactivos(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Obtener clientes con estado=False (eliminados lógicamente)
    clientes = Cliente.objects.filter(estado=False).order_by('-id_cliente')
    return render(request, 'clientes/lista_inactivos.html', {'clientes': clientes})


def restaurar_cliente(request, id):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Obtener cliente inactivo y restaurarlo
    cliente = get_object_or_404(Cliente, id_cliente=id, estado=False)
    cliente.estado = True
    cliente.save()
    
    messages.success(request, f'✅ Cliente "{cliente.nombre}" restaurado exitosamente')
    return redirect('clientes:clientes_inactivos')