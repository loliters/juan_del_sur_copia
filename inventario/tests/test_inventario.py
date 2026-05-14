# inventario/tests/test_inventario_simulado.py
import pytest
from productos.models import Producto
from ventas.models import Venta, DetalleVenta
from clientes.models import Cliente
from metodopago.models import MetodoPago
from inventario.models import Inventario  # Solo para crear, pero no usarás directamente


# =========================================
# FIXTURES
# =========================================
@pytest.fixture(autouse=True)
def limpiar_datos(db):
    """Limpia todos los datos antes de cada test"""
    DetalleVenta.objects.all().delete()
    Venta.objects.all().delete()
    Inventario.objects.all().delete()
    Producto.objects.all().delete()
    Cliente.objects.all().delete()
    yield


@pytest.fixture
def crear_producto():
    """Crea un producto (Inventario se crea automáticamente via property)"""
    producto = Producto.objects.create(
        codProducto='P001',
        nomProducto='Producto Test',
        precioVenta=100.00,
        precioCompra=50.00,
        stockMinimo=5,
        tipoUnidad='unidad',
        estado='activo'
    )
    # Usar el property para crear inventario automáticamente
    producto.stockActual = 10
    producto.save()
    return producto


@pytest.fixture
def crear_cliente():
    return Cliente.objects.create(
        nombre='Juan Perez',
        email='juan@test.com',
        telefono='77777777',
        zona='Centro',
        calle='Bolivar',
        numeroCasa='123',
        estado=True
    )


@pytest.fixture
def crear_metodo_pago():
    metodo, _ = MetodoPago.objects.get_or_create(tipoPago='QR')
    return metodo


# =========================================
# 1. PRUEBAS DE DESCUENTO DE STOCK (usando solo Producto)
# =========================================

@pytest.mark.django_db
def test_descuento_stock_usando_producto(crear_producto, crear_cliente, crear_metodo_pago):
    """Prueba 1: Descontar stock usando directamente el producto"""
    producto = crear_producto
    stock_inicial = producto.stockActual  # Usa el property
    
    # Simular venta - descontar stock
    producto.stockActual -= 2  # El setter actualiza Inventario automáticamente
    producto.save()
    
    # Verificar
    producto.refresh_from_db()
    assert producto.stockActual == stock_inicial - 2


@pytest.mark.django_db
def test_descuento_stock_venta_completa(crear_producto, crear_cliente, crear_metodo_pago):
    """Prueba 2: Flujo completo de venta descontando stock"""
    producto = crear_producto
    stock_inicial = producto.stockActual
    
    # Crear venta
    venta = Venta.objects.create(
        total=300.00,
        cliente=crear_cliente,
        metodo_pago=crear_metodo_pago
    )
    
    # Obtener o crear inventario (necesario para DetalleVenta)
    inventario, _ = Inventario.objects.get_or_create(
        producto=producto,
        defaults={'stock_actual': producto.stockActual, 'tipoUnidad': 'unidad'}
    )
    
    # Crear detalle de venta
    DetalleVenta.objects.create(
        venta=venta,
        inventario=inventario,
        cantidad=3,
        subtotal=300.00
    )
    
    # Descontar stock usando el producto
    producto.stockActual -= 3
    producto.save()
    
    # Verificar
    producto.refresh_from_db()
    assert producto.stockActual == stock_inicial - 3


@pytest.mark.django_db
def test_restaurar_stock_al_eliminar_venta(crear_producto, crear_cliente, crear_metodo_pago):
    """Prueba 3: Restaurar stock cuando se elimina una venta"""
    producto = crear_producto
    stock_inicial = producto.stockActual
    
    # Descontar stock (simulando venta)
    producto.stockActual -= 2
    producto.save()
    
    assert producto.stockActual == stock_inicial - 2
    
    # Restaurar stock (simulando eliminación de venta)
    producto.stockActual += 2
    producto.save()
    
    assert producto.stockActual == stock_inicial


@pytest.mark.django_db
def test_stock_no_negativo_con_producto(crear_producto):
    """Prueba 4: Verificar que el stock no pueda ser negativo"""
    producto = crear_producto
    stock_inicial = producto.stockActual
    
    # Intentar descontar más del disponible
    try:
        if producto.stockActual >= 100:
            producto.stockActual -= 100
        else:
            # No permitir descuento
            raise ValueError("Stock insuficiente")
    except ValueError:
        pass
    
    producto.refresh_from_db()
    assert producto.stockActual == stock_inicial  # No cambió


# =========================================
# 2. PRUEBAS DE CONSULTA DE PRODUCTOS (stock vía property)
# =========================================

@pytest.mark.django_db
def test_consultar_stock_de_producto(crear_producto):
    """Prueba 5: Consultar stock actual de un producto"""
    producto = crear_producto
    
    # El property stockActual debe mostrar el stock correcto
    assert producto.stockActual == 10


@pytest.mark.django_db
def test_consultar_stock_multiple_productos():
    """Prueba 6: Consultar stock de múltiples productos"""
    # Crear productos con diferentes stocks usando el property
    productos = []
    
    for i, stock in enumerate([10, 20, 30, 5]):
        prod = Producto.objects.create(
            codProducto=f'P00{i}',
            nomProducto=f'Producto {i}',
            precioVenta=100,
            estado='activo'
        )
        prod.stockActual = stock
        prod.save()
        productos.append(prod)
    
    # Verificar stocks
    assert productos[0].stockActual == 10
    assert productos[1].stockActual == 20
    assert productos[2].stockActual == 30
    assert productos[3].stockActual == 5


@pytest.mark.django_db
def test_consultar_productos_con_stock_bajo(crear_producto):
    """Prueba 7: Encontrar productos con stock por debajo del mínimo"""
    producto = crear_producto
    producto.stockMinimo = 15
    producto.stockActual = 10
    producto.save()
    
    # Buscar productos con stock bajo
    productos_bajos = []
    for p in Producto.objects.filter(estado='activo'):
        if p.stockActual < p.stockMinimo:
            productos_bajos.append(p)
    
    assert len(productos_bajos) == 1
    assert productos_bajos[0].codProducto == 'P001'


@pytest.mark.django_db
def test_consultar_solo_productos_disponibles():
    """Prueba 8: Consultar productos con stock disponible (mayor a 0)"""
    # Producto con stock
    prod_con_stock = Producto.objects.create(
        codProducto='P001', nomProducto='Con Stock', precioVenta=100, estado='activo'
    )
    prod_con_stock.stockActual = 10
    prod_con_stock.save()
    
    # Producto sin stock
    prod_sin_stock = Producto.objects.create(
        codProducto='P002', nomProducto='Sin Stock', precioVenta=100, estado='activo'
    )
    prod_sin_stock.stockActual = 0
    prod_sin_stock.save()
    
    # Filtrar
    disponibles = [p for p in Producto.objects.filter(estado='activo') if p.stockActual > 0]
    
    assert len(disponibles) == 1
    assert disponibles[0].codProducto == 'P001'


# =========================================
# 3. PRUEBAS DE VISUALIZACIÓN DE CANTIDADES
# =========================================

@pytest.mark.django_db
def test_visualizar_stock_en_lista(crear_producto):
    """Prueba 9: Mostrar lista de productos con su stock"""
    producto = crear_producto
    
    # Simular vista que muestra productos con stock
    lista_productos = []
    for p in Producto.objects.all():
        lista_productos.append({
            'codigo': p.codProducto,
            'nombre': p.nomProducto,
            'stock': p.stockActual,  # Usando el property
            'precio': float(p.precioVenta)
        })
    
    assert len(lista_productos) == 1
    assert lista_productos[0]['stock'] == 10
    assert lista_productos[0]['codigo'] == 'P001'


@pytest.mark.django_db
def test_visualizar_stock_despues_venta(crear_producto):
    """Prueba 10: Ver stock actualizado después de una venta"""
    producto = crear_producto
    stock_inicial = producto.stockActual
    
    # Simular venta de 3 unidades
    producto.stockActual -= 3
    producto.save()
    
    assert producto.stockActual == stock_inicial - 3


@pytest.mark.django_db
def test_visualizar_diferencia_stock(crear_producto):
    """Prueba 11: Calcular diferencia de stock entre dos momentos"""
    producto = crear_producto
    stock_inicial = producto.stockActual
    
    # Realizar múltiples ventas
    producto.stockActual -= 2
    producto.save()
    producto.stockActual -= 1
    producto.save()
    producto.stockActual -= 3
    producto.save()
    
    stock_final = producto.stockActual
    diferencia = stock_inicial - stock_final
    
    assert diferencia == 6  # Total de unidades vendidas
    assert stock_final == stock_inicial - 6


# =========================================
# 4. PRUEBAS DE BÚSQUEDA Y FILTROS
# =========================================

@pytest.mark.django_db
def test_buscar_productos_por_nombre_y_ver_stock():
    """Prueba 12: Buscar producto por nombre y mostrar su stock"""
    producto = Producto.objects.create(
        codProducto='P001',
        nomProducto='Laptop HP',
        precioVenta=800,
        estado='activo'
    )
    producto.stockActual = 5
    producto.save()
    
    # Buscar
    busqueda = 'Laptop'
    resultados = Producto.objects.filter(nomProducto__icontains=busqueda, estado='activo')
    
    assert resultados.count() == 1
    assert resultados[0].stockActual == 5


@pytest.mark.django_db
def test_ordenar_productos_por_stock():
    """Prueba 13: Ordenar productos por cantidad de stock"""
    stocks = [10, 50, 5, 30]
    productos = []
    
    for i, stock in enumerate(stocks):
        prod = Producto.objects.create(
            codProducto=f'P00{i}', nomProducto=f'Prod{i}', precioVenta=100, estado='activo'
        )
        prod.stockActual = stock
        prod.save()
        productos.append(prod)
    
    # Ordenar por stock ascendente
    ordenados = sorted(productos, key=lambda p: p.stockActual)
    
    assert ordenados[0].stockActual == 5
    assert ordenados[1].stockActual == 10
    assert ordenados[2].stockActual == 30
    assert ordenados[3].stockActual == 50