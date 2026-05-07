from django.db import models
from proveedores.models import Proveedor
from productos.models import Producto
from inventario.models import Inventario


# Create your models here.
class Compra(models.Model):
    """
    Representa la cabecera de la compra.
    Relación 1:N con Proveedor (Un proveedor tiene muchas compras).
    """
    id_compra = models.AutoField(primary_key=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField() 
    estado = models.BooleanField(default=False)
    # Relación 1:N 
    proveedor = models.ForeignKey(
        Proveedor, 
        on_delete=models.CASCADE, 
        related_name='compras_realizadas'
    )

    def __str__(self):
        return f"Compra #{self.id_compra} - Total: {self.total}"

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"


class DetalleCompra(models.Model):
    """
    Esta es la tabla intermedia (Entidad Asociativa) que resuelve la relación N:M
    entre Compras e Inventarios.
    """
    id_detalle_compra = models.AutoField(primary_key=True)
    cantidad = models.IntegerField() # O DecimalField si manejas decimales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    # Relación con la tabla Compra
    compra = models.ForeignKey(
        Compra, 
        on_delete=models.CASCADE, 
        related_name='detalles'
    )

    # Relación con la tabla Inventario
    inventario = models.ForeignKey(
        Inventario, 
        on_delete=models.CASCADE,
        related_name='detalles_compra'
    )

    def __str__(self):
        return f"Detalle {self.id_detalle_compra} (Cant: {self.cantidad})"

    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal antes de guardar"""
        if self.inventario and self.inventario.producto:
            # Subtotal = cantidad × precio de compra del producto
            self.subtotal = self.cantidad * self.inventario.producto.precioCompra
        else:
            self.subtotal = 0
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "Detalle de Compra"
        verbose_name_plural = "Detalles de Compras"