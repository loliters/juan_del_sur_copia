# ventas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Venta, DetalleVenta
from metodopago.models import MetodoPago
from clientes.models import Cliente
from inventario.models import Inventario
from productos.models import Producto
from django.db import models  # ← Agregar al inicio del archivo

# ========================
# CRUD DE VENTAS (Administrador)
# ========================

def ver_ventas(request):
    # Verificar sesión
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Obtener todas las ventas con sus relaciones
    ventas = Venta.objects.select_related('cliente', 'metodo_pago').all().order_by('-fecha')
    
    # Para cada venta, calcular los detalles
    ventas_con_detalles = []
    for venta in ventas:
        detalles = DetalleVenta.objects.filter(venta=venta).select_related('inventario__producto')
        
        ventas_con_detalles.append({
            'venta': venta,
            'detalles': detalles,
        })
    
    return render(request, 'ventas/ver_ventas.html', {
        'ventas': ventas_con_detalles,
        'es_cajero': request.session.get('rol') == 'cajero',
    })


def editar_venta(request, id):
    # Verificar sesión - cualquier usuario logueado puede editar
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # ❌ ELIMINA ESTAS LÍNEAS:
    # if request.session.get('rol') != "administrador":
    #     messages.error(request, '❌ Solo el administrador puede editar ventas')
    #     return redirect('ventas:ver_ventas')
    
    venta = get_object_or_404(Venta, id_venta=id)
    
    if request.method == "POST":
        cliente_id = request.POST.get('cliente_id')
        metodo_pago_id = request.POST.get('metodo_pago_id')
        
        errores = False
        
        if not cliente_id:
            messages.error(request, 'Debe seleccionar un cliente')
            errores = True
        
        if not metodo_pago_id:
            messages.error(request, 'Debe seleccionar un método de pago')
            errores = True
        
        if not errores:
            try:
                cliente = Cliente.objects.get(id_cliente=cliente_id)
                metodo_pago = MetodoPago.objects.get(id_met_pago=metodo_pago_id)
                
                venta.cliente = cliente
                venta.metodo_pago = metodo_pago
                venta.save()
                
                messages.success(request, f'✅ Venta #{venta.id_venta} actualizada exitosamente')
                return redirect('ventas:ver_ventas')
                
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente no encontrado')
            except MetodoPago.DoesNotExist:
                messages.error(request, 'Método de pago no encontrado')
    
    clientes = Cliente.objects.filter(estado=True)
    metodos_pago = MetodoPago.objects.all()
    detalles = DetalleVenta.objects.filter(venta=venta).select_related('inventario__producto')
    
    return render(request, 'ventas/editar_venta.html', {
        'venta': venta,
        'clientes': clientes,
        'metodos_pago': metodos_pago,
        'detalles': detalles,
    })
def eliminar_venta(request, id):
    # Verificar sesión - cualquier usuario logueado puede eliminar
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # ❌ ELIMINA ESTAS LÍNEAS:
    # if request.session.get('rol') != "administrador":
    #     messages.error(request, '❌ Solo el administrador puede eliminar ventas')
    #     return redirect('ventas:ver_ventas')
    
    venta = get_object_or_404(Venta, id_venta=id)
    
    if request.method == "POST":
        try:
            # Devolver stock al producto
            detalles = DetalleVenta.objects.filter(venta=venta).select_related('inventario__producto')
            for detalle in detalles:
                producto = detalle.inventario.producto
                producto.stockActual += detalle.cantidad
                producto.save()
            
            # Eliminar detalles y venta
            detalles.delete()
            venta.delete()
            
            messages.success(request, f'✅ Venta #{id} eliminada y stock restaurado')
            return redirect('ventas:ver_ventas')
            
        except Exception as e:
            messages.error(request, f'❌ Error al eliminar venta: {str(e)}')
    
    return render(request, 'ventas/eliminar_venta.html', {'venta': venta})
# ========================
# CARRITO DE COMPRAS
# ========================

def agregar_al_carrito(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cantidad = int(request.POST.get('cantidad', 1))
        
        producto = get_object_or_404(Producto, codProducto=producto_id)
        
        if producto.stockActual < cantidad:
            messages.error(request, f'Stock insuficiente para {producto.nomProducto}')
            return redirect('dashboard_cajero')
        
        carrito = request.session.get('carrito', {'items': [], 'total': 0})
        
        encontrado = False
        for item in carrito['items']:
            if item.get('cod') == producto_id:
                nueva_cantidad = item['cantidad'] + cantidad
                if nueva_cantidad > producto.stockActual:
                    messages.error(request, f'Stock insuficiente para {producto.nomProducto}')
                    return redirect('dashboard_cajero')
                item['cantidad'] = nueva_cantidad
                item['subtotal'] = item['precio'] * item['cantidad']
                encontrado = True
                break
        
        if not encontrado:
            carrito['items'].append({
                'cod': producto.codProducto,  # ← Guardar cod
                'id': producto.id,
                'nombre': producto.nomProducto,
                'precio': float(producto.precioVenta),
                'cantidad': cantidad,
                'subtotal': float(producto.precioVenta) * cantidad
            })
        
        carrito['total'] = sum(item['subtotal'] for item in carrito['items'])
        carrito['subtotal'] = carrito['total']
        
        request.session['carrito'] = carrito
        messages.success(request, f' Agregado {producto.nomProducto} al carrito')
    
    return redirect('dashboard_cajero')
def eliminar_del_carrito(request, cod):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Obtener carrito de sesión
    carrito = request.session.get('carrito', {'items': [], 'total': 0})
    
    # Filtrar el producto a eliminar por 'cod' (codProducto)
    carrito['items'] = [item for item in carrito['items'] if item.get('cod') != cod]
    
    # Recalcular total
    carrito['total'] = sum(item.get('subtotal', 0) for item in carrito['items'])
    carrito['subtotal'] = carrito['total']
    
    # Guardar carrito en sesión
    request.session['carrito'] = carrito
    
    messages.success(request, '✅ Producto eliminado del carrito')
    return redirect('dashboard_cajero')


def seleccionar_cliente(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Manejar selección de cliente
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        if cliente_id:
            cliente = get_object_or_404(Cliente, id_cliente=cliente_id, estado=True)
            request.session['cliente_venta'] = cliente.id_cliente
            messages.success(request, f'✅ Cliente {cliente.nombre} seleccionado')
        else:
            request.session['cliente_venta'] = None
            messages.info(request, 'Venta sin cliente registrado')
        return redirect('dashboard_cajero')
    
    # GET - Mostrar clientes con búsqueda
    query = request.GET.get('q', '').strip()
    clientes = Cliente.objects.filter(estado=True).order_by('nombre')
    
    if query:
        # Buscar por carnet (exacto o parcial) o por nombre
        clientes = clientes.filter(
            models.Q(carnet__icontains=query) |  # Buscar por carnet
            models.Q(nombre__icontains=query)     # Buscar por nombre
        )
    
    return render(request, 'ventas/seleccionar_cliente.html', {
        'clientes': clientes,
        'query': query,
    })


def registro_venta(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    carrito = request.session.get('carrito', {'items': [], 'total': 0})
    
    if not carrito['items']:
        messages.error(request, '❌ El carrito está vacío')
        return redirect('dashboard_cajero')
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago', 'QR')
        cliente_id = request.session.get('cliente_venta')
        
        try:
            # Verificar stock nuevamente
            for item in carrito['items']:
                producto = Producto.objects.get(id=item['id'])
                if producto.stockActual < item['cantidad']:
                    messages.error(request, f'Stock insuficiente para {producto.nomProducto}')
                    return redirect('dashboard_cajero')
            
            # Obtener o crear método de pago
            metodo, _ = MetodoPago.objects.get_or_create(tipoPago=metodo_pago)
            
            # Obtener cliente
            cliente = None
            if cliente_id:
                cliente = Cliente.objects.filter(id_cliente=cliente_id, estado=True).first()
            
            # Crear venta
            venta = Venta.objects.create(
                total=carrito['total'],
                cliente=cliente,
                metodo_pago=metodo
            )
            
            # Crear detalles y descontar stock
            for item in carrito['items']:
                producto = Producto.objects.get(id=item['id'])
                producto.stockActual -= item['cantidad']
                producto.save()
                
                # Buscar o crear inventario
                inventario, _ = Inventario.objects.get_or_create(
                    producto=producto,
                    defaults={'stock_actual': producto.stockActual, 'tipoUnidad': 'unidad'}
                )
                inventario.stock_actual = producto.stockActual
                inventario.save()
                
                DetalleVenta.objects.create(
                    venta=venta,
                    inventario=inventario,
                    cantidad=item['cantidad'],
                    subtotal=item['subtotal']
                )
            
            # Limpiar carrito y cliente
            request.session['carrito'] = {'items': [], 'total': 0}
            request.session['cliente_venta'] = None
            
            messages.success(request, f'✅ Venta #{venta.id_venta} registrada por ${venta.total}')
            
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
        
        return redirect('dashboard_cajero')
    
    return redirect('dashboard_cajero')