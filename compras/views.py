from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Compra, DetalleCompra
from proveedores.models import Proveedor
from inventario.models import Inventario
from productos.models import Producto
from datetime import datetime
import json
from datetime import date
import urllib.parse  # ← Para decodificar URLs


# ========================
# VER COMPRAS (Listado Principal)
# ========================

def ver_compras(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    compras = Compra.objects.filter(estado=True).select_related('proveedor').all().order_by('-fecha')
    
    compras_con_detalles = []
    for compra in compras:
        detalles = DetalleCompra.objects.filter(compra=compra).select_related('inventario__producto')
        detalles_con_subtotal = []
        for detalle in detalles:
            precio = _obtener_precio_compra(detalle)
            subtotal = precio * detalle.cantidad
            detalles_con_subtotal.append({
                'detalle': detalle,
                'precio_unitario': precio,
                'subtotal': subtotal
            })
        compras_con_detalles.append({
            'compra': compra,
            'detalles': detalles_con_subtotal,
        })
    
    return render(request, 'compras/ver_compras.html', {
        'compras': compras_con_detalles,
    })


# ========================
# CREAR COMPRA (REABASTECIMIENTO - SUMA STOCK)
# ========================

def crear_compra(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    base_context = {
        'proveedores': Proveedor.objects.filter(estado=True),
        'productos_disponibles': Producto.objects.filter(estado__iexact='Activo'),
    }
    
    if request.method == "POST":
        # 📥 Parsear fecha CON HORA
        fecha_str = request.POST.get('fecha')
        fecha_compra = None
        if fecha_str:
            try:
                fecha_compra = datetime.fromisoformat(fecha_str)
            except ValueError:
                try:
                    fecha_compra = datetime.strptime(fecha_str, '%Y-%m-%d')
                except ValueError:
                    fecha_compra = datetime.now()
        else:
            fecha_compra = datetime.now()

        proveedor_id = request.POST.get('proveedor_id')
        productos_data = request.POST.getlist('productos')
        
        # 🔍 DEBUG (opcional, para ver qué llega)
        # print(f"\n🛒 DEBUG: productos_data count: {len(productos_data)}")

        base_context['proveedor_seleccionado'] = proveedor_id
        base_context['fecha_seleccionada'] = fecha_str

        if not proveedor_id:
            messages.error(request, 'Debe seleccionar un proveedor')
            return render(request, 'compras/crear_compra.html', base_context)
        
        # ✅ Validar productos (manejando URL-encoded JSON)
        if not productos_data:
            messages.error(request, 'Debe agregar al menos un producto')
            return render(request, 'compras/crear_compra.html', base_context)
        
        productos_validos = []
        for p in productos_data:
            p_stripped = p.strip()
            if p_stripped and p_stripped not in ['', 'null', 'undefined', '[]']:
                productos_validos.append(p_stripped)
        
        if not productos_validos:
            messages.error(request, 'Debe agregar al menos un producto')
            return render(request, 'compras/crear_compra.html', base_context)
        
        try:
            proveedor = Proveedor.objects.get(id=proveedor_id)
            total_compra = 0
            detalles_a_crear = []
            
            for item_json in productos_validos:
                try:
                    # ✅ Decodificar si viene URL-encoded
                    if '%' in item_json:
                        item_json = urllib.parse.unquote(item_json)
                    
                    item = json.loads(item_json)
                    cod = item.get('cod')
                    if not cod:
                        continue
                    
                    cantidad = int(item.get('cantidad', 1))
                    precio_compra = float(item.get('precio_compra', 0))
                    subtotal = cantidad * precio_compra
                    total_compra += subtotal
                    
                    producto = Producto.objects.get(codProducto=cod)
                    inventario, _ = Inventario.objects.get_or_create(
                        producto=producto,
                        defaults={'stock_actual': producto.stockActual, 'tipoUnidad': 'unidad'}
                    )
                    
                    detalles_a_crear.append({
                        'inventario': inventario,
                        'cantidad': cantidad,
                        'precio_compra': precio_compra
                    })
                except (json.JSONDecodeError, Producto.DoesNotExist, ValueError, KeyError):
                    continue
            
            if not detalles_a_crear:
                messages.error(request, 'No se encontraron productos válidos')
                return render(request, 'compras/crear_compra.html', base_context)
            
            compra = Compra.objects.create(
                total=total_compra,
                fecha=fecha_compra,
                proveedor=proveedor,
                estado=True
            )
            
            for detalle_data in detalles_a_crear:
                DetalleCompra.objects.create(
                    compra=compra,
                    inventario=detalle_data['inventario'],
                    cantidad=detalle_data['cantidad']
                )
                producto = detalle_data['inventario'].producto
                producto.stockActual += detalle_data['cantidad']
                producto.save()
                detalle_data['inventario'].stock_actual = producto.stockActual
                detalle_data['inventario'].save()
            
            if 'carrito_compra' in request.session:
                del request.session['carrito_compra']
            
            messages.success(request, f'✅ Compra #{compra.id_compra} registrada - Stock reabastecido correctamente')
            return redirect('compras:ver_compras')
            
        except Proveedor.DoesNotExist:
            messages.error(request, 'Proveedor no encontrado')
        except Exception as e:
            messages.error(request, f'Error al crear compra: {str(e)}')
            import traceback
            traceback.print_exc()
    
    return render(request, 'compras/crear_compra.html', base_context)



# ========================
# EDITAR COMPRA (AJUSTE DE STOCK)
# ========================

def editar_compra(request, id):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    
    compra = get_object_or_404(Compra, id_compra=id)
    detalles_actuales = DetalleCompra.objects.filter(compra=compra).select_related('inventario__producto')
    
    base_context = {
        'compra': compra,
        'proveedores': Proveedor.objects.filter(estado=True),
        'productos_disponibles': Producto.objects.filter(estado__iexact='Activo'),
    }
    
    # Preparar productos existentes para el frontend
    productos_existentes = []
    for detalle in detalles_actuales:
        precio = _obtener_precio_compra(detalle)
        productos_existentes.append({
            'cod': detalle.inventario.producto.codProducto,
            'nombre': detalle.inventario.producto.nomProducto,
            'cantidad': detalle.cantidad,
            'precio_compra': precio,
            'subtotal': precio * detalle.cantidad
        })
    base_context['productos_existentes_json'] = json.dumps(productos_existentes)
    
    if request.method == "POST":
        # ✅ Parsear fecha CON HORA
        fecha_str = request.POST.get('fecha')
        if fecha_str:
            try:
                compra.fecha = datetime.fromisoformat(fecha_str)
            except ValueError:
                compra.fecha = datetime.strptime(fecha_str, '%Y-%m-%d')

        proveedor_id = request.POST.get('proveedor_id')
        productos_data = request.POST.getlist('productos')
        
        if not proveedor_id:
            messages.error(request, 'Debe seleccionar un proveedor')
            return render(request, 'compras/editar_compra.html', base_context)
        
        # ✅ Validar productos
        if not productos_data:
            messages.error(request, 'Debe agregar al menos un producto')
            return render(request, 'compras/editar_compra.html', base_context)
        
        productos_validos = []
        for p in productos_data:
            p_stripped = p.strip()
            if p_stripped and p_stripped not in ['', 'null', 'undefined', '[]']:
                productos_validos.append(p_stripped)
        
        if not productos_validos:
            messages.error(request, 'Debe agregar al menos un producto')
            return render(request, 'compras/editar_compra.html', base_context)
        
        try:
            proveedor = Proveedor.objects.get(id=proveedor_id)
            nuevos_productos = {}
            
            for item_json in productos_validos:
                try:
                    # ✅ Decodificar si viene URL-encoded
                    if '%' in item_json:
                        item_json = urllib.parse.unquote(item_json)
                    
                    item = json.loads(item_json)
                    cod = item.get('cod')
                    if not cod:
                        continue
                    cantidad = int(item.get('cantidad', 1))
                    precio_compra = float(item.get('precio_compra', 0))
                    nuevos_productos[cod] = {'cantidad': cantidad, 'precio_compra': precio_compra}
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
            
            if not nuevos_productos:
                messages.error(request, 'No se encontraron productos válidos')
                return render(request, 'compras/editar_compra.html', base_context)
            
            compra.proveedor = proveedor
            
            detalles_dict = {d.inventario.producto.codProducto: d for d in detalles_actuales}
            total_compra = 0
            
            # ❌ Eliminar productos que ya no están
            for cod, detalle in list(detalles_dict.items()):
                if cod not in nuevos_productos:
                    producto = detalle.inventario.producto
                    producto.stockActual -= detalle.cantidad
                    producto.save()
                    detalle.inventario.stock_actual = producto.stockActual
                    detalle.inventario.save()
                    detalle.delete()
            
            # ➕ Actualizar o agregar productos
            for cod, data in nuevos_productos.items():
                try:
                    producto = Producto.objects.get(codProducto=cod)
                    cantidad = data['cantidad']
                    precio_compra = data['precio_compra']
                    total_compra += cantidad * precio_compra
                    
                    inventario, _ = Inventario.objects.get_or_create(
                        producto=producto,
                        defaults={'stock_actual': producto.stockActual, 'tipoUnidad': 'unidad'}
                    )
                    
                    if cod in detalles_dict:
                        detalle = detalles_dict[cod]
                        diferencia = cantidad - detalle.cantidad
                        if diferencia > 0:
                            producto.stockActual += diferencia
                        elif diferencia < 0:
                            producto.stockActual -= abs(diferencia)
                        producto.save()
                        inventario.stock_actual = producto.stockActual
                        inventario.save()
                        detalle.cantidad = cantidad
                        detalle.save()
                    else:
                        producto.stockActual += cantidad
                        producto.save()
                        inventario.stock_actual = producto.stockActual
                        inventario.save()
                        DetalleCompra.objects.create(
                            compra=compra,
                            inventario=inventario,
                            cantidad=cantidad
                        )
                except Producto.DoesNotExist:
                    continue
                except Exception as e:
                    print(f"Error al procesar producto {cod}: {e}")
                    continue
            
            compra.total = total_compra
            compra.save()
            
            messages.success(request, f'✅ Compra #{compra.id_compra} actualizada correctamente')
            return redirect('compras:ver_compras')
            
        except Proveedor.DoesNotExist:
            messages.error(request, 'Proveedor no encontrado')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
            import traceback
            traceback.print_exc()
    
    return render(request, 'compras/editar_compra.html', base_context)



# ====================
# ELIMINAR COMPRA (DESHACER REABASTECIMIENTO)
# ========================

def eliminar_compra(request, id):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    compra = get_object_or_404(Compra, id_compra=id)
    if request.method == "POST":
        try:
            detalles = DetalleCompra.objects.filter(compra=compra).select_related('inventario__producto')
            for detalle in detalles:
                producto = detalle.inventario.producto
                producto.stockActual -= detalle.cantidad
                producto.save()
                detalle.inventario.stock_actual = producto.stockActual
                detalle.inventario.save()
            compra.estado = False
            compra.save()
            messages.success(request, f'Compra #{id} eliminada y stock ajustado')
            return redirect('compras:ver_compras')
        except Exception as e:
            messages.error(request, f' Error al desactivar compra: {str(e)}')
    return render(request, 'compras/eliminar_compra.html', {'compra': compra})

# ========================
# COMPRAS DESACTIVADAS
# ========================

def compras_eliminadas(request):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    compras = Compra.objects.filter(estado=False).select_related('proveedor').order_by('-fecha')
    compras_con_detalles = []
    for compra in compras:
        detalles = DetalleCompra.objects.filter(compra=compra).select_related('inventario__producto')
        detalles_con_subtotal = []
        for detalle in detalles:
            precio = _obtener_precio_compra(detalle)
            subtotal = precio * detalle.cantidad
            detalles_con_subtotal.append({'detalle': detalle, 'precio_unitario': precio, 'subtotal': subtotal})
        compras_con_detalles.append({'compra': compra, 'detalles': detalles_con_subtotal})
    return render(request, 'compras/compras_eliminadas.html', {'compras': compras_con_detalles})

# ========================
# ACTIVAR COMPRA (REHACER REABASTECIMIENTO)
# ========================

def activar_compra(request, id):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    compra = get_object_or_404(Compra, id_compra=id)
    try:
        detalles = DetalleCompra.objects.filter(compra=compra).select_related('inventario__producto')
        for detalle in detalles:
            producto = detalle.inventario.producto
            producto.stockActual += detalle.cantidad
            producto.save()
            detalle.inventario.stock_actual = producto.stockActual
            detalle.inventario.save()
        compra.estado = True
        compra.save()
        messages.success(request, f'Compra #{id} activada y stock reabastecido')
        return redirect('compras:compras_desactivadas')
    except Exception as e:
        messages.error(request, f' Error al activar compra: {str(e)}')
        return redirect('compras:compras_desactivadas')

# ========================
# FUNCIÓN AUXILIAR: Obtener precio de compra
# ========================

def _obtener_precio_compra(detalle):
    producto = detalle.inventario.producto
    if hasattr(producto, 'precioCompra') and producto.precioCompra:
        return float(producto.precioCompra)
    if hasattr(producto, 'precioVenta') and producto.precioVenta:
        return float(producto.precioVenta)
    return 0.0

# ========================
# AJAX - AGREGAR AL CARRITO DE COMPRA
# ========================

@require_http_methods(["POST"])
def agregar_al_carrito_compra_ajax(request):
    if request.session.get('usuario_id') is None:
        return JsonResponse({'success': False, 'error': 'Sesión no iniciada'}, status=401)
    producto_id = request.POST.get('producto_id')
    cantidad = int(request.POST.get('cantidad', 1))
    precio_compra = float(request.POST.get('precio_compra', 0))
    try:
        producto = Producto.objects.get(codProducto=producto_id, estado__iexact='Activo')
        carrito = request.session.get('carrito_compra', {'items': [], 'total': 0})
        encontrado = False
        for item in carrito['items']:
            if str(item.get('cod')) == str(producto_id):
                item['cantidad'] += cantidad
                item['subtotal'] = item['precio_compra'] * item['cantidad']
                encontrado = True
                break
        if not encontrado:
            carrito['items'].append({
                'cod': producto.codProducto, 'id': producto.id, 'nombre': producto.nomProducto,
                'precio_compra': precio_compra, 'cantidad': cantidad, 'subtotal': precio_compra * cantidad
            })
        carrito['total'] = sum(item['subtotal'] for item in carrito['items'])
        request.session['carrito_compra'] = carrito
        return JsonResponse({'success': True, 'message': f'Agregado {producto.nomProducto}', 'cart_items_count': len(carrito['items']), 'cart_total': carrito['total']})
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Producto no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ========================
# AJAX - ACTUALIZAR CANTIDAD
# ========================

@require_http_methods(["POST"])
def actualizar_cantidad_carrito_compra(request):
    if request.session.get('usuario_id') is None:
        return JsonResponse({'success': False, 'error': 'Sesión no iniciada'}, status=401)
    producto_cod = request.POST.get('producto_cod')
    nueva_cantidad = int(request.POST.get('cantidad', 1))
    if nueva_cantidad < 1:
        return JsonResponse({'success': False, 'error': 'Cantidad inválida'})
    carrito = request.session.get('carrito_compra', {'items': [], 'total': 0})
    item_encontrado = None
    for item in carrito['items']:
        if str(item.get('cod')) == str(producto_cod):
            item['cantidad'] = nueva_cantidad
            item['subtotal'] = item['precio_compra'] * nueva_cantidad
            item_encontrado = item
            break
    if not item_encontrado:
        return JsonResponse({'success': False, 'error': 'Producto no encontrado'})
    carrito['total'] = sum(item['subtotal'] for item in carrito['items'])
    request.session['carrito_compra'] = carrito
    return JsonResponse({'success': True, 'item_subtotal': item_encontrado['subtotal'], 'cart_total': carrito['total'], 'cart_items_count': len(carrito['items'])})

# ========================
# AJAX - ELIMINAR DEL CARRITO
# ========================

@require_http_methods(["POST"])
def eliminar_del_carrito_compra_ajax(request):
    if request.session.get('usuario_id') is None:
        return JsonResponse({'success': False, 'error': 'Sesión no iniciada'}, status=401)
    producto_cod = request.POST.get('producto_cod')
    carrito = request.session.get('carrito_compra', {'items': [], 'total': 0})
    carrito['items'] = [item for item in carrito['items'] if str(item.get('cod')) != str(producto_cod)]
    carrito['total'] = sum(item.get('subtotal', 0) for item in carrito['items'])
    request.session['carrito_compra'] = carrito
    return JsonResponse({'success': True, 'cart_total': carrito['total'], 'cart_items_count': len(carrito['items'])})

# ========================
# AJAX - BUSCAR PRODUCTOS
# ========================

def buscar_productos_compra_ajax(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'success': False, 'productos': []})
    try:
        productos = Producto.objects.filter(
            models.Q(codProducto__icontains=query) | models.Q(nomProducto__icontains=query),
            estado__iexact='Activo' 
        )[:10]
        data = []
        for p in productos:
            precio_compra = getattr(p, 'precioCompra', None)
            if precio_compra is None:
                precio_compra = getattr(p, 'precioVenta', 0)
            data.append({
                'codProducto': str(p.codProducto) if p.codProducto else '',
                'nomProducto': p.nomProducto if p.nomProducto else '',
                'precioCompra': float(precio_compra) if precio_compra else 0.0,
                'stockActual': int(p.stockActual) if p.stockActual else 0
            })
        return JsonResponse({'success': True, 'productos': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ========================
# RECUPERAR COMPRA (Compatible con urls antiguas)
# ========================

def recuperar_compra(request, id):
    if request.session.get('usuario_id') is None:
        return redirect('login')
    compra = get_object_or_404(Compra, id_compra=id)
    try:
        detalles = DetalleCompra.objects.filter(compra=compra).select_related('inventario__producto')
        for detalle in detalles:
            producto = detalle.inventario.producto
            producto.stockActual += detalle.cantidad
            producto.save()
            detalle.inventario.stock_actual = producto.stockActual
            detalle.inventario.save()
        compra.estado = True
        compra.save()
        messages.success(request, f'✅ Compra #{id} recuperada exitosamente')
        return redirect('compras:compras_desactivadas')
    except Exception as e:
        messages.error(request, f' Error al recuperar compra: {str(e)}')
        return redirect('compras:compras_desactivadas')

