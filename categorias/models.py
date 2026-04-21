from django.db import models

class Categoria(models.Model):
    nomCategoria = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nomCategoria