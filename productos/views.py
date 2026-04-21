from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Producto
from categorias.models import Categoria
from decimal import Decimal

# Listar productos (Inventario)
def inventario(request):
    # Mostrar solo productos activos
    productos = Producto.objects.filter(estado='activo')
    return render(request, 'productos/inventario.html', {'productos': productos})

# Registrar nuevo producto
def registrar(request):
    if request.method == 'POST':
        codProducto = request.POST.get('codProducto')
        nomProducto = request.POST.get('nomProducto')
        #categoria = request.POST.get('categoria')
        categoria_id = request.POST.get('categoria')
        categoria = get_object_or_404(Categoria, id=categoria_id)

        precioCompra = request.POST.get('precioCompra')
        precioVenta = request.POST.get('precioVenta')
        stockActual = request.POST.get('stockActual')
        tipoUnidad = request.POST.get('tipoUnidad')

        
        if not nomProducto:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('productos:registrar')
        
        producto = Producto.objects.create(
            codProducto=codProducto,
            nomProducto=nomProducto,
            categoria=categoria,  # YA ES OBJETO
            precioCompra=precioCompra,
            precioVenta=precioVenta,
            stockActual=stockActual,
            tipoUnidad=tipoUnidad,
            estado='activo'
        )



        messages.success(request, f'Producto "{nomProducto}" creado exitosamente')
        return redirect('productos:inventario')
    
    #categorias = ["Lacteos", "Pan", "Frutas", "Bebidas", "Snacks", "General"]
    categorias = Categoria.objects.filter(estado=True)
    unidades = ["Litros", "Kilos", "Gramos", "Paquete", "Bolsa", "General"]
    
    return render(request, 'productos/registrar.html', {'categorias': categorias,'unidades': unidades})

# Editar producto
def editar(request, id_producto):
    producto = get_object_or_404(Producto, id=id_producto)
    #categorias = ["Lacteos", "Pan", "Frutas", "Bebidas", "Snacks", "General"]
    categorias = Categoria.objects.filter(estado=True)
    unidades = ["Litros", "Kilos", "Gramos", "Paquete", "Bolsa", "General"]
    
    
    if request.method == 'POST':
        producto.nomProducto = request.POST.get('nomProducto')
        categoria_id = request.POST.get('categoria')
        producto.categoria = get_object_or_404(Categoria, id=categoria_id)
        producto.tipoUnidad = request.POST.get('tipoUnidad')
        
        # Convertir precios correctamente
        precio_compra_str = request.POST.get('precioCompra', '0')
        precio_venta_str = request.POST.get('precioVenta', '0')
        
        # Reemplazar coma por punto si existe
        precio_compra_str = precio_compra_str.replace(',', '.')
        precio_venta_str = precio_venta_str.replace(',', '.')
        
        # Convertir a Decimal
        try:
            producto.precioCompra = Decimal(precio_compra_str) if precio_compra_str else 0.0
            producto.precioVenta = Decimal(precio_venta_str) if precio_venta_str else 0.0
        except ValueError:
            producto.precioCompra = 0.0
            producto.precioVenta = 0.0

            
        
        # Convertir stock a entero
        stock_str = request.POST.get('stockActual', '0')
        try:
            producto.stockActual = int(stock_str) if stock_str else 0
        except ValueError:
            producto.stockActual = 0
        
        producto.estado = request.POST.get('estado')
        
        if not producto.nomProducto:
            messages.error(request, 'El nombre es obligatorio')
            return redirect('productos:editar', id_producto=id_producto)
        
        producto.save()
        messages.success(request, f'Producto "{producto.nomProducto}" actualizado')
        return redirect('productos:inventario')
    
    return render(request, 'productos/editar.html', {
        'producto': producto,
        'categorias': categorias,
        'unidades': unidades
    })

# Cambiar estado a inactivo (en lugar de eliminar)
def eliminar(request, id_producto):
    producto = get_object_or_404(Producto, id=id_producto)
    
    if request.method == 'POST':
        nomProducto = producto.nomProducto
        # Cambiar estado a 'inactivo' en lugar de eliminar
        producto.estado = 'inactivo'  
        producto.save()
        messages.success(request, f'Producto "{nomProducto}" marcado como inactivo')
        return redirect('productos:inventario')
    
    return render(request, 'productos/eliminar.html', {'producto': producto})

# Para la recuperación - Vista para ver la lista de inactivos
def lista_recuperar(request):
    # Filtramos los que están en la "papelera" (Inactivos)
    productos_inactivos = Producto.objects.filter(estado='inactivo')  # ← minúscula
    return render(request, 'productos/recuperar.html', {'productos': productos_inactivos})

# Función lógica para activar el producto
def ejecutar_recuperacion(request, id_producto):
    producto = get_object_or_404(Producto, id=id_producto)
    producto.estado = 'activo'  # ← minúscula
    producto.save()
    messages.success(request, f"¡{producto.nomProducto} ha vuelto al inventario!")  # ← nombre, no nom_producto
    return redirect('productos:lista_recuperar')  # ← nombre correcto de la URL


    # =========================
# LOGOUT
# =========================
def logout_view(request):

    request.session.flush()
    return redirect('login')
#==========================