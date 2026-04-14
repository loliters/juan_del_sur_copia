from django.db import models
from decimal import Decimal

# Create your models here.

class Producto(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre del producto")
    categoria = models.CharField(max_length=100, default="General", verbose_name="Categoría")
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de compra")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de venta")
    stock = models.IntegerField(default=0, verbose_name="Stock disponible") #esta con esto porque es una cagada hacerlo de otra manera
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre
    
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']