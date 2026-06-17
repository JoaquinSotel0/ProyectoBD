from django.contrib import admin
from .models import Sala, Requerimiento, Reservacion, HistorialReservacion


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad', 'orden', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)


@admin.register(Requerimiento)
class RequerimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_evento',
        'nombre_registra',
        'fecha_evento',
        'hora_inicio',
        'hora_fin',
        'asistentes',
        'estatus',
        'fecha_creacion',
    )
    list_filter = ('estatus', 'fecha_evento', 'salas')
    search_fields = ('nombre_evento', 'nombre_registra')
    filter_horizontal = ('salas', 'requerimientos')


@admin.register(HistorialReservacion)
class HistorialReservacionAdmin(admin.ModelAdmin):
    list_display = ('reservacion', 'usuario', 'accion', 'fecha_accion')
    list_filter = ('accion', 'fecha_accion')
    search_fields = ('reservacion__nombre_evento', 'usuario__username', 'accion')