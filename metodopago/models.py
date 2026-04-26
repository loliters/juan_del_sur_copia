# metodopago/models.py
from django.db import models

class MetodoPago(models.Model):
    id_met_pago = models.AutoField(primary_key=True)
    tipoPago = models.CharField(max_length=50)

    def __str__(self):
        return self.tipoPago

    class Meta:
        db_table = 'metodo_pago'
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'