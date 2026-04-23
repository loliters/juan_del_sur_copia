# ventas/models.py

from django.db import models
from clientes.models import Cliente
from inventario.models import Inventario
from django.contrib.auth.models import User  # usuario del sistema

class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='ventas'
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
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