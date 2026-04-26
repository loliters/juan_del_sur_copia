# ventas/models.py
from django.db import models
from clientes.models import Cliente
from metodopago.models import MetodoPago  # ← Importar desde metodopago
from inventario.models import Inventario

class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # 🔥 FK a Cliente
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='ventas'
    )

    # 🔥 FK a MetodoPago
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ventas'
    )

    def __str__(self):
        return f"Venta {self.id_venta} - {self.fecha}"


class DetalleVenta(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    cantidad = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.CASCADE,
        related_name='detalles_venta'
    )

    def __str__(self):
        return f"Detalle Venta {self.id_detalle}"