# clientes/models.py

from django.db import models

class MetodoPago(models.Model):
    id_met_pago = models.AutoField(primary_key=True)
    tipoPago = models.CharField(max_length=50)

    def __str__(self):
        return self.tipoPago


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    razonSocial = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    zona = models.CharField(max_length=100)
    calle = models.CharField(max_length=100)
    numeroCasa = models.CharField(max_length=20)
    estado = models.BooleanField(default=True)

    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clientes'
    )

    def __str__(self):
        return self.nombre