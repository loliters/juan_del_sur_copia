from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Cliente  # Vas a crear este modelo

def registro_cliente(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    if request.method == "POST":
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        
        if not nombre:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('registro_cliente')
        
        # Guardar cliente
        cliente = Cliente.objects.create(
            nombre=nombre,
            email=email,
            telefono=telefono
        )
        
        messages.success(request, f'Cliente {nombre} registrado')
        return redirect('lista_clientes')
    
    return render(request, 'clientes/registro_cliente.html')

def lista_clientes(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    clientes = Cliente.objects.filter(estado=True)
    return render(request, 'clientes/lista_clientes.html', {'clientes': clientes})