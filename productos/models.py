# productos/models.py
from django.db import models
from decimal import Decimal
from categorias.models import Categoria
from usuarios.models import Usuario

class Producto(models.Model):

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    codProducto = models.CharField(
        max_length=45,
        unique=True,
        verbose_name="Código de Producto",
        null=True,
        blank=True  
    )

    nomProducto = models.CharField(
        max_length=100,
        verbose_name="Nombre del Producto"
    )

    precioCompra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')  
    )

    precioVenta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    stockActual = models.IntegerField(default=0)  # ← Mantener stockActual

    stockMinimo = models.IntegerField(default=0)  # ← AGREGAR stockMinimo

    tipoUnidad = models.CharField(
        max_length=100,
        default='unidad'
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='activo'
    )

    # RELACIÓN CON CATEGORÍA
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # RELACIÓN CON USUARIO
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos'
    )

    def __str__(self):
        return self.nomProducto

    class Meta:
        db_table = 'productos'
        ordering = ['nomProducto']