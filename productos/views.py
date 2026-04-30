from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto
from categorias.models import Categoria
from decimal import Decimal


# =========================
# LISTAR PRODUCTOS (INVENTARIO)
# =========================
def inventario(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')

    productos = Producto.objects.filter(estado='activo')

    # 👇 AQUÍ EL CAMBIO
    if request.session.get('rol') == 'cajero':
        return render(request, 'productos/lista.html', {
            'productos': productos
        })

    # ADMIN
    return render(request, 'productos/inventario.html', {
        'productos': productos
    })


# =========================
# REGISTRAR PRODUCTO
# =========================
def registrar(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')

    # 👇 SOLO ADMIN
    if request.session.get('rol') != 'administrador':
        messages.error(request, 'Acceso denegado')
        return redirect('productos:inventario')

    if request.method == 'POST':
        codProducto = request.POST.get('codProducto')
        nomProducto = request.POST.get('nomProducto')
        categoria_id = request.POST.get('categoria')
        categoria = get_object_or_404(Categoria, id=categoria_id)

        precioCompra = request.POST.get('precioCompra')
        precioVenta = request.POST.get('precioVenta')
        stockActual = request.POST.get('stockActual')
        tipoUnidad = request.POST.get('tipoUnidad')

        if not nomProducto:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('productos:registrar')
        
        Producto.objects.create(
            codProducto=codProducto,
            nomProducto=nomProducto,
            categoria=categoria,
            precioCompra=precioCompra,
            precioVenta=precioVenta,
            stockActual=stockActual,
            tipoUnidad=tipoUnidad,
            estado='activo'
        )

        messages.success(request, f'Producto "{nomProducto}" creado')
        return redirect('productos:inventario')
    
    categorias = Categoria.objects.filter(estado=True)
    unidades = ["Litros", "Kilos", "Gramos", "Paquete", "Bolsa", "General"]
    
    return render(request, 'productos/registrar.html', {
        'categorias': categorias,
        'unidades': unidades
    })


# =========================
# EDITAR PRODUCTO
# =========================
def editar(request, id_producto):
    if request.session.get('usuario_id') is None:
        return redirect('login')

    # 👇 SOLO ADMIN
    if request.session.get('rol') != 'administrador':
        messages.error(request, 'Acceso denegado')
        return redirect('productos:inventario')

    producto = get_object_or_404(Producto, id=id_producto)
    categorias = Categoria.objects.filter(estado=True)
    unidades = ["Litros", "Kilos", "Gramos", "Paquete", "Bolsa", "General"]
    
    if request.method == 'POST':
        producto.nomProducto = request.POST.get('nomProducto')
        categoria_id = request.POST.get('categoria')
        producto.categoria = get_object_or_404(Categoria, id=categoria_id)
        producto.tipoUnidad = request.POST.get('tipoUnidad')
        
        # Precios
        try:
            producto.precioCompra = Decimal(request.POST.get('precioCompra', '0').replace(',', '.'))
            producto.precioVenta = Decimal(request.POST.get('precioVenta', '0').replace(',', '.'))
        except:
            producto.precioCompra = 0
            producto.precioVenta = 0

        # Stock
        try:
            producto.stockActual = int(request.POST.get('stockActual', 0))
        except:
            producto.stockActual = 0
        
        producto.estado = request.POST.get('estado')

        if not producto.nomProducto:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('productos:editar', id_producto=id_producto)
        
        producto.save()
        messages.success(request, 'Producto actualizado')
        return redirect('productos:inventario')
    
    return render(request, 'productos/editar.html', {
        'producto': producto,
        'categorias': categorias,
        'unidades': unidades
    })


# =========================
# ELIMINAR (INACTIVAR)
# =========================
def eliminar(request, id_producto):
    if request.session.get('usuario_id') is None:
        return redirect('login')

    # 👇 SOLO ADMIN
    if request.session.get('rol') != 'administrador':
        messages.error(request, 'Acceso denegado')
        return redirect('productos:inventario')

    producto = get_object_or_404(Producto, id=id_producto)
    
    if request.method == 'POST':
        producto.estado = 'inactivo'
        producto.save()
        messages.success(request, 'Producto eliminado')
        return redirect('productos:inventario')
    
    return render(request, 'productos/eliminar.html', {'producto': producto})


# =========================
# RECUPERAR
# =========================
def lista_recuperar(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')

    if request.session.get('rol') != 'administrador':
        return redirect('productos:inventario')

    productos = Producto.objects.filter(estado='inactivo')
    return render(request, 'productos/recuperar.html', {'productos': productos})


def ejecutar_recuperacion(request, id_producto):
    if request.session.get('usuario_id') is None:
        return redirect('login')

    if request.session.get('rol') != 'administrador':
        return redirect('productos:inventario')

    producto = get_object_or_404(Producto, id=id_producto)
    producto.estado = 'activo'
    producto.save()

    return redirect('productos:lista_recuperar')


# =========================
# LOGOUT
# =========================
def logout_view(request):
    request.session.flush()
    return redirect('login')