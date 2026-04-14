from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Producto

# Listar productos (Inventario)
def inventario(request):
    # Mostrar solo productos activos
    productos = Producto.objects.filter(estado='activo')
    # para mostrar todos: productos = Producto.objects.all()
    return render(request, 'productos/inventario.html', {'productos': productos})

# Registrar nuevo producto
def registrar(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        categoria = request.POST.get('categoria')
        precio_compra = request.POST.get('precio_compra')
        precio_venta = request.POST.get('precio_venta')
        stock = request.POST.get('stock')
        
        if not nombre:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('productos:registrar')
        
        producto = Producto.objects.create(
            nombre=nombre,
            categoria=categoria,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            stock=stock,
            estado='activo'
        )
        
        messages.success(request, f'Producto "{nombre}" creado exitosamente')
        return redirect('productos:inventario')
    
    categorias = ["Lacteos", "Pan", "Frutas", "Bebidas", "Snacks", "General"]
    return render(request, 'productos/registrar.html', {'categorias': categorias})

# Editar producto
def editar(request, id_producto):
    producto = get_object_or_404(Producto, id=id_producto)
    categorias = ["Lacteos", "Pan", "Frutas", "Bebidas", "Snacks", "General"]
    
    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre')
        producto.categoria = request.POST.get('categoria')
        producto.precio_compra = request.POST.get('precio_compra')
        producto.precio_venta = request.POST.get('precio_venta')
        producto.stock = request.POST.get('stock')
        producto.estado = request.POST.get('estado')
        
        if not producto.nombre:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('productos:editar', id_producto=id_producto)
        
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" actualizado')
        return redirect('productos:inventario')
    
    return render(request, 'productos/editar.html', {
        'producto': producto,
        'categorias': categorias
    })

# Cambiar estado a inactivo (en lugar de eliminar)
def eliminar(request, id_producto):
    producto = get_object_or_404(Producto, id=id_producto)
    
    if request.method == 'POST':
        nombre = producto.nombre
        # Cambiar estado a 'inactivo' en lugar de eliminar
        producto.estado = 'inactivo'
        producto.save()
        messages.success(request, f'Producto "{nombre}" marcado como inactivo')
        return redirect('productos:inventario')
    
    return render(request, 'productos/eliminar.html', {'producto': producto})