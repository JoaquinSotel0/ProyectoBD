from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import time


class Sala(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    capacidad = models.PositiveIntegerField(default=40)
    orden = models.PositiveSmallIntegerField(unique=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Requerimiento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Reservacion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('FINALIZADA', 'Finalizada'),
    ]

    ACOMODOS_SILLAS = [
        ('HERRADURA', 'Herradura'),
        ('SALON', 'Salón (solo sillas)'),
        ('AULA', 'Aula (sillas y mesas)'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    nombre_registra = models.CharField(max_length=100)
    nombre_evento = models.CharField(max_length=150)
    fecha_evento = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    asistentes = models.PositiveIntegerField()
    salas = models.ManyToManyField(Sala)
    requerimientos = models.ManyToManyField(Requerimiento, blank=True)
    acomodo_sillas = models.CharField(max_length=20, choices=ACOMODOS_SILLAS, default='SALON')
    estatus = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        if self.hora_inicio < time(8, 0):
            raise ValidationError("La hora de inicio no puede ser antes de las 08:00.")

        if self.hora_fin > time(20, 0):
            raise ValidationError("La hora de fin no puede ser después de las 20:00.")

        if self.hora_fin <= self.hora_inicio:
            raise ValidationError("La hora de fin debe ser posterior a la hora de inicio.")

        if self.fecha_evento.weekday() >= 5:
            raise ValidationError("Solo se permiten reservaciones de lunes a viernes.")

    def __str__(self):
        return self.nombre_evento


class HistorialReservacion(models.Model):
    reservacion = models.ForeignKey(Reservacion, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    accion = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    fecha_accion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.accion} - {self.reservacion.nombre_evento}'
