from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto
from categorias.models import Categoria
from decimal import Decimal

# 👇 IMPORTA TU MODELO INVENTARIO (ajusta la ruta si está en otra app)
try:
    from inventario.models import Inventario
except ImportError:
    # Si Inventario está en la misma app 'productos', descomenta la siguiente línea:
    # from .models import Inventario
    pass


# =========================
# LISTAR PRODUCTOS (INVENTARIO)
# =========================
def inventario(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')

    # 👇 prefetch_related carga los inventarios en la misma consulta (evita N+1)
    productos = Producto.objects.filter(estado='activo').prefetch_related('inventarios')

    if request.session.get('rol') == 'cajero':
        return render(request, 'productos/lista.html', {'productos': productos})

    return render(request, 'productos/inventario.html', {'productos': productos})

# =========================
# REGISTRAR PRODUCTO
# =========================
def registrar(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')

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
        stockActual = request.POST.get('stockActual', '0')
        tipoUnidad = request.POST.get('tipoUnidad')

        if not nomProducto:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('productos:registrar')
        
        # 1️⃣ Crear Producto 
        producto = Producto.objects.create(
            codProducto=codProducto,
            nomProducto=nomProducto,
            categoria=categoria,
            precioCompra=Decimal(precioCompra.replace(',', '.') if precioCompra else '0.00'),
            precioVenta=Decimal(precioVenta.replace(',', '.') if precioVenta else '0.00'),
            tipoUnidad=tipoUnidad,
            estado='activo',
            usuario_id=request.session.get('usuario_id')
        )

        # 2️⃣ Crear registro en Inventario
        try:
            stock_val = int(stockActual)
        except (ValueError, TypeError):
            stock_val = 0

        Inventario.objects.create(
            producto=producto,
            stock_actual=stock_val,
            tipoUnidad=tipoUnidad
        )

        messages.success(request, f'Producto "{nomProducto}" creado')
        
        # 🎯 REDIRECCIÓN INTELIGENTE: Volver a compra si viene de ahí
        next_url = request.GET.get('next')
        if next_url:
            # Reconstruir URL con parámetros para mantener contexto de compra
            proveedor = request.GET.get('proveedor')
            fecha = request.GET.get('fecha')
            
            if proveedor or fecha:
                separator = '&' if '?' in next_url else '?'
                params = []
                if proveedor:
                    params.append(f'proveedor_id={proveedor}')
                if fecha:
                    params.append(f'fecha={fecha}')
                next_url += separator + '&'.join(params)
            
            return redirect(next_url)
        
        # Si no viene de compra, redirigir al inventario normal
        return redirect('productos:inventario')
    
    # Para GET: pasar categorías, unidades, etc.
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
        except Exception:
            producto.precioCompra = Decimal('0.00')
            producto.precioVenta = Decimal('0.00')

        producto.estado = request.POST.get('estado')

        if not producto.nomProducto:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('productos:editar', id_producto=id_producto)
        
        producto.save()

        # 👇 ACTUALIZAR/CREAR REGISTRO EN INVENTARIO
        try:
            nuevo_stock = int(request.POST.get('stockActual', 0))
        except (ValueError, TypeError):
            nuevo_stock = 0

        inv, created = Inventario.objects.get_or_create(
            producto=producto,
            defaults={'stock_actual': nuevo_stock, 'tipoUnidad': producto.tipoUnidad}
        )
        if not created:
            inv.stock_actual = nuevo_stock
            inv.save()
        
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

    productos = Producto.objects.filter(estado='inactivo').prefetch_related('inventarios')
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