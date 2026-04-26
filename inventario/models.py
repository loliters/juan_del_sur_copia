# inventario/models.py
from django.db import models
from productos.models import Producto

class Inventario(models.Model):
    id_inven = models.AutoField(primary_key=True)
    stock_actual = models.IntegerField()  # Stock actual
    tipoUnidad = models.CharField(max_length=50)

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='inventarios'
    )

    def __str__(self):
        return f"{self.producto.nomProducto} - Stock: {self.stock_actual}"