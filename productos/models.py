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

    # PROPIEDAD PARA LEER/ESCRIBIR STOCK DESDE INVENTARIO
    @property
    def stockActual(self):

        # Un producto puede tener VARIOS registros 
        from django.db.models import Sum
        total = self.inventarios.aggregate(total=Sum('stock_actual'))['total']
        return total or 0

    @stockActual.setter
    def stockActual(self, value):
        """Actualiza el stock en Inventario (crea el registro si no existe)"""
        inv, created = self.inventarios.get_or_create(
            # campos requeridos 
            defaults={'stock_actual': value}
        )
        if not created:
            inv.stock_actual = value
            inv.save()

    def __str__(self):
        return self.nomProducto

    class Meta:
        db_table = 'productos'
        ordering = ['nomProducto']