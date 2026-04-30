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

#Editar venta
def editar_venta(request, id):
    # Verificar sesión - cualquier usuario logueado puede editar
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    venta = get_object_or_404(Venta, id_venta=id)
    
    # Obtener detalles actuales
    detalles_actuales = DetalleVenta.objects.filter(venta=venta).select_related('inventario__producto')
    
    if request.method == "POST":
        cliente_id = request.POST.get('cliente_id')
        metodo_pago_id = request.POST.get('metodo_pago_id')
        productos_data = request.POST.getlist('productos')
        
        # ========== DEBUG ==========
        print("=" * 60)
        print("EDITAR VENTA - POST RECIBIDO")
        print(f"Venta ID: {id}")
        print(f"Cliente ID: {cliente_id}")
        print(f"Método Pago ID: {metodo_pago_id}")
        print(f"Total productos recibidos: {len(productos_data)}")
        for i, p in enumerate(productos_data):
            print(f"  Producto {i+1}: {p}")
        print("=" * 60)
        # ========== FIN DEBUG ==========
        
        errores = False
        
        if not cliente_id:
            messages.error(request, 'Debe seleccionar un cliente')
            errores = True
        
        if not metodo_pago_id:
            messages.error(request, 'Debe seleccionar un método de pago')
            errores = True
        
        if not productos_data:
            messages.error(request, 'Debe agregar al menos un producto')
            errores = True
        
        if not errores:
            try:
                import json
                import re
                
                cliente = Cliente.objects.get(id_cliente=cliente_id)
                metodo_pago = MetodoPago.objects.get(id_met_pago=metodo_pago_id)
                
                venta.cliente = cliente
                venta.metodo_pago = metodo_pago
                
                # Procesar productos del formulario
                nuevos_productos = {}
                
                for item_json in productos_data:
                    try:
                        # Limpiar el JSON
                        item_json = item_json.strip()
                        if not item_json or item_json == 'null' or item_json == 'undefined':
                            print(f"  Saltando item vacío: {item_json}")
                            continue
                        
                        # Intentar parsear el JSON
                        # Reemplazar comillas simples por dobles si es necesario
                        item_json = item_json.replace("'", '"')
                        item = json.loads(item_json)
                        
                        cod = item.get('cod')
                        if not cod:
                            print(f"  Producto sin código: {item}")
                            continue
                            
                        cantidad = int(item.get('cantidad', 1))
                        precio = float(item.get('precio', 0))
                        
                        nuevos_productos[cod] = {'cantidad': cantidad, 'precio': precio}
                        print(f"  ✓ Producto procesado: {cod} - Cantidad: {cantidad} - Precio: {precio}")
                        
                    except json.JSONDecodeError as e:
                        print(f"  ✗ Error JSON en: {item_json}")
                        print(f"    Error: {e}")
                        continue
                    except (ValueError, KeyError) as e:
                        print(f"  ✗ Error en datos: {e} - Item: {item_json}")
                        continue
                
                print(f"Total productos válidos: {len(nuevos_productos)}")
                
                if not nuevos_productos:
                    messages.error(request, 'No se encontraron productos válidos')
                    return redirect('ventas:editar_venta', id=id)
                
                # Diccionario de detalles actuales
                detalles_dict = {d.inventario.producto.codProducto: d for d in detalles_actuales}
                total_venta = 0
                
                # 1. Eliminar productos que ya no están en la nueva lista
                for cod, detalle in list(detalles_dict.items()):
                    if cod not in nuevos_productos:
                        try:
                            # Restaurar stock
                            producto = detalle.inventario.producto
                            producto.stockActual += detalle.cantidad
                            producto.save()
                            
                            inventario = detalle.inventario
                            inventario.stock_actual = producto.stockActual
                            inventario.save()
                            
                            detalle.delete()
                            print(f"  ✓ Producto eliminado: {cod}")
                        except Exception as e:
                            print(f"  ✗ Error eliminando detalle {cod}: {e}")
                
                # 2. Actualizar o crear nuevos productos
                for cod, data in nuevos_productos.items():
                    try:
                        producto = Producto.objects.get(codProducto=cod)
                        cantidad = data['cantidad']
                        precio = data['precio']
                        subtotal = cantidad * precio
                        total_venta += subtotal
                        
                        # Obtener o crear inventario
                        inventario, _ = Inventario.objects.get_or_create(
                            producto=producto,
                            defaults={'stock_actual': producto.stockActual, 'tipoUnidad': 'unidad'}
                        )
                        
                        if cod in detalles_dict:
                            # Actualizar producto existente
                            detalle = detalles_dict[cod]
                            diferencia = cantidad - detalle.cantidad
                            
                            if diferencia > 0:
                                # Se necesita más stock
                                if producto.stockActual < diferencia:
                                    messages.error(request, f'Stock insuficiente para {producto.nomProducto}. Disponible: {producto.stockActual}, Necesita: {diferencia}')
                                    return redirect('ventas:editar_venta', id=id)
                                producto.stockActual -= diferencia
                            elif diferencia < 0:
                                # Se devuelve stock
                                producto.stockActual += abs(diferencia)
                            
                            producto.save()
                            inventario.stock_actual = producto.stockActual
                            inventario.save()
                            
                            detalle.cantidad = cantidad
                            detalle.subtotal = subtotal
                            detalle.save()
                            print(f"  ✓ Detalle actualizado: {cod} - Cantidad: {cantidad}")
                        else:
                            # Crear nuevo producto
                            if producto.stockActual < cantidad:
                                messages.error(request, f'Stock insuficiente para {producto.nomProducto}. Disponible: {producto.stockActual}, Necesita: {cantidad}')
                                return redirect('ventas:editar_venta', id=id)
                            
                            producto.stockActual -= cantidad
                            producto.save()
                            inventario.stock_actual = producto.stockActual
                            inventario.save()
                            
                            DetalleVenta.objects.create(
                                venta=venta,
                                inventario=inventario,
                                cantidad=cantidad,
                                subtotal=subtotal
                            )
                            print(f"  ✓ Nuevo detalle creado: {cod}")
                            
                    except Producto.DoesNotExist:
                        messages.error(request, f'Producto con código {cod} no encontrado')
                        continue
                    except Exception as e:
                        print(f"  ✗ Error procesando producto {cod}: {e}")
                        messages.error(request, f'Error procesando producto: {str(e)}')
                        return redirect('ventas:editar_venta', id=id)
                
                # Guardar el total de la venta
                venta.total = total_venta
                venta.save()
                print(f"Total calculado: {total_venta}")
                print(f"Total guardado en venta: {venta.total}")
                
                # Limpiar carrito de sesión si existe
                if 'carrito' in request.session:
                    del request.session['carrito']
                
                messages.success(request, f'✓ Venta #{venta.id_venta} actualizada exitosamente - Total: Bs {venta.total:.2f}')
                return redirect('ventas:ver_ventas')
                
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente no encontrado')
            except MetodoPago.DoesNotExist:
                messages.error(request, 'Método de pago no encontrado')
            except Exception as e:
                messages.error(request, f'Error al actualizar: {str(e)}')
                print(f"Error general: {e}")
                import traceback
                traceback.print_exc()
    # ==================== GET - Mostrar formulario (CORREGIDO) ====================
    clientes = Cliente.objects.filter(estado=True)
    metodos_pago = MetodoPago.objects.all()
    detalles = DetalleVenta.objects.filter(venta=venta).select_related('inventario__producto')
    productos_disponibles = Producto.objects.filter(estado='activo')
    
    # Calcular precio_unitario para cada detalle
    for detalle in detalles:
        # Asegurar que subtotal sea un número
        subtotal = float(detalle.subtotal) if detalle.subtotal else 0.0
        cantidad = int(detalle.cantidad) if detalle.cantidad else 1
        
        if cantidad > 0 and subtotal > 0:
            detalle.precio_unitario = round(subtotal / cantidad, 2)
        else:
            # Si no se puede calcular, usar el precio del producto del inventario
            precio_producto = float(detalle.inventario.producto.precioVenta) if detalle.inventario.producto.precioVenta else 0.0
            detalle.precio_unitario = round(precio_producto, 2)
            # También actualizar el subtotal si estaba mal
            if subtotal == 0 and cantidad > 0:
                detalle.subtotal = cantidad * precio_producto
                detalle.save()
                print(f"  - Subtotal corregido de {detalle.inventario.producto.nomProducto}: {detalle.subtotal}")
        
        # FORZAR que precio_unitario sea un número válido (nunca None)
        if detalle.precio_unitario is None or detalle.precio_unitario == 0:
            detalle.precio_unitario = float(detalle.inventario.producto.precioVenta) if detalle.inventario.producto.precioVenta else 0.0
        
        # Debug detallado
        print(f"Producto cargado: {detalle.inventario.producto.nomProducto}")
        print(f"  - Cantidad: {detalle.cantidad}")
        print(f"  - Subtotal: {detalle.subtotal}")
        print(f"  - Precio unitario: {detalle.precio_unitario}")
        print(f"  - Tipo precio: {type(detalle.precio_unitario)}")
        print("-" * 40)
    
    return render(request, 'ventas/editar_venta.html', {
        'venta': venta,
        'clientes': clientes,
        'metodos_pago': metodos_pago,
        'detalles': detalles,
        'productos_disponibles': productos_disponibles,
    })

#eliminar ventas
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
            
            messages.success(request, f' Venta #{id} eliminada y stock restaurado')
            return redirect('ventas:ver_ventas')
            
        except Exception as e:
            messages.error(request, f' Error al eliminar venta: {str(e)}')
    
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
    
    messages.success(request, ' Producto eliminado del carrito')
    return redirect('dashboard_cajero')


def seleccionar_cliente(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        
        # Si no hay cliente_id, mostrar error
        if not cliente_id:
            messages.error(request, ' Debes seleccionar un cliente para continuar')
            return redirect('dashboard_cajero')
        
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    # Manejar selección de cliente
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        if cliente_id:
            cliente = get_object_or_404(Cliente, id_cliente=cliente_id, estado=True)
            request.session['cliente_venta'] = cliente.id_cliente
            messages.success(request, f' Cliente {cliente.nombre} seleccionado')
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
        messages.error(request, ' El carrito está vacío')
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
            
            messages.success(request, f' Venta #{venta.id_venta} registrada por Bs{venta.total}')
            
        except Exception as e:
            messages.error(request, f' Error: {str(e)}')
        
        return redirect('dashboard_cajero')
    
    return redirect('dashboard_cajero')
#nuevas cosas
# ventas/views.py

# ventas/views.py - Agrega estas funciones al final del archivo

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from productos.models import Producto

# ========================
# AJAX - AGREGAR AL CARRITO
# ========================
@require_http_methods(["POST"])
def agregar_al_carrito_ajax(request):
    """Agrega un producto al carrito vía AJAX"""
    if request.session.get('usuario_id') is None:
        return JsonResponse({'success': False, 'error': 'Sesión no iniciada'}, status=401)
    
    producto_id = request.POST.get('producto_id')
    cantidad = int(request.POST.get('cantidad', 1))
    
    try:
        producto = Producto.objects.get(codProducto=producto_id, estado='activo')
        
        if producto.stockActual < cantidad:
            return JsonResponse({'success': False, 'error': f'Stock insuficiente para {producto.nomProducto}'})
        
        carrito = request.session.get('carrito', {'items': [], 'total': 0, 'subtotal': 0})
        
        encontrado = False
        for item in carrito['items']:
            if str(item.get('cod')) == str(producto_id):
                nueva_cantidad = item['cantidad'] + cantidad
                if nueva_cantidad > producto.stockActual:
                    return JsonResponse({'success': False, 'error': f'No hay suficiente stock de {producto.nomProducto}'})
                item['cantidad'] = nueva_cantidad
                item['subtotal'] = item['precio'] * nueva_cantidad
                encontrado = True
                break
        
        if not encontrado:
            carrito['items'].append({
                'cod': producto.codProducto,
                'id': producto.id,
                'nombre': producto.nomProducto,
                'precio': float(producto.precioVenta),
                'cantidad': cantidad,
                'subtotal': float(producto.precioVenta) * cantidad
            })
        
        carrito['subtotal'] = sum(item['subtotal'] for item in carrito['items'])
        carrito['total'] = carrito['subtotal']
        
        request.session['carrito'] = carrito
        
        return JsonResponse({
            'success': True,
            'message': f'Agregado {producto.nomProducto} al carrito',
            'cart_items_count': len(carrito['items']),
            'cart_subtotal': carrito['subtotal'],
            'cart_total': carrito['total']
        })
        
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Producto no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========================
# AJAX - ACTUALIZAR CANTIDAD
# ========================
@require_http_methods(["POST"])
def actualizar_cantidad_carrito(request):
    """Actualiza la cantidad de un producto en el carrito vía AJAX"""
    if request.session.get('usuario_id') is None:
        return JsonResponse({'success': False, 'error': 'Sesión no iniciada'}, status=401)
    
    producto_cod = request.POST.get('producto_cod')
    nueva_cantidad = int(request.POST.get('cantidad', 1))
    
    if nueva_cantidad < 1:
        return JsonResponse({'success': False, 'error': 'La cantidad debe ser mayor a 0'})
    
    carrito = request.session.get('carrito', {'items': [], 'total': 0, 'subtotal': 0})
    
    item_encontrado = None
    for item in carrito['items']:
        if str(item.get('cod')) == str(producto_cod):
            # Verificar stock
            try:
                producto = Producto.objects.get(codProducto=producto_cod)
                if producto.stockActual < nueva_cantidad:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Stock insuficiente. Solo hay {producto.stockActual} unidades disponibles'
                    })
            except Producto.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Producto no encontrado'})
            
            item['cantidad'] = nueva_cantidad
            item['subtotal'] = item['precio'] * nueva_cantidad
            item_encontrado = item
            break
    
    if not item_encontrado:
        return JsonResponse({'success': False, 'error': 'Producto no encontrado en el carrito'})
    
    carrito['subtotal'] = sum(item['subtotal'] for item in carrito['items'])
    carrito['total'] = carrito['subtotal']
    
    request.session['carrito'] = carrito
    
    return JsonResponse({
        'success': True,
        'item_subtotal': item_encontrado['subtotal'],
        'cart_subtotal': carrito['subtotal'],
        'cart_total': carrito['total'],
        'cart_items_count': len(carrito['items'])
    })


# ========================
# AJAX - ELIMINAR DEL CARRITO
# ========================
@require_http_methods(["POST"])
def eliminar_del_carrito_ajax(request):
    """Elimina un producto del carrito vía AJAX"""
    if request.session.get('usuario_id') is None:
        return JsonResponse({'success': False, 'error': 'Sesión no iniciada'}, status=401)
    
    producto_cod = request.POST.get('producto_cod')
    
    carrito = request.session.get('carrito', {'items': [], 'total': 0, 'subtotal': 0})
    
    carrito['items'] = [item for item in carrito['items'] 
                        if str(item.get('cod')) != str(producto_cod)]
    
    carrito['subtotal'] = sum(item.get('subtotal', 0) for item in carrito['items'])
    carrito['total'] = carrito['subtotal']
    
    request.session['carrito'] = carrito
    
    return JsonResponse({
        'success': True,
        'cart_subtotal': carrito['subtotal'],
        'cart_total': carrito['total'],
        'cart_items_count': len(carrito['items'])
    })
# ========================
# AJAX - BUSCAR PRODUCTOS
# ========================
def buscar_productos_ajax(request):
    """API para buscar productos (usado en editar venta)"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '').strip()
        if query:
            productos = Producto.objects.filter(
                nomProducto__icontains=query,
                estado='activo'
            )[:10]
            data = [{
                'codProducto': p.codProducto,
                'nomProducto': p.nomProducto,
                'precioVenta': float(p.precioVenta),
                'stockActual': p.stockActual
            } for p in productos]
            return JsonResponse({'success': True, 'productos': data})
    return JsonResponse({'success': False, 'productos': []})