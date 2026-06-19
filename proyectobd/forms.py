from django import forms
from .models import Reservacion, Sala, Requerimiento
from datetime import time

HORARIOS_RESERVA = [
    (time(hora, 0), f'{hora:02d}:00')
    for hora in range(8, 21)
]

class ReservacionForm(forms.ModelForm):
    class Meta:
        model = Reservacion
        fields = [
            'nombre_registra',
            'nombre_evento',
            'fecha_evento',
            'hora_inicio',
            'hora_fin',
            'asistentes',
            'salas',
            'requerimientos',
            'acomodo_sillas',
            'observaciones',
        ]
        widgets = {
            'nombre_registra': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del solicitante',
            }),
            'nombre_evento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del evento',
            }),
            'fecha_evento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'hora_inicio': forms.Select(attrs={
                'class': 'form-control',
            }),
            'hora_fin': forms.Select(attrs={
                'class': 'form-control',
            }),
            'asistentes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
            }),
            'salas': forms.CheckboxSelectMultiple(),
            'requerimientos': forms.CheckboxSelectMultiple(),
            'acomodo_sillas': forms.Select(attrs={
                'class': 'form-control',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales',
            }),
        }
        labels = {
            'nombre_registra': 'Nombre del solicitante',
            'nombre_evento': 'Nombre del evento',
            'fecha_evento': 'Fecha del evento',
            'hora_inicio': 'Hora de inicio',
            'hora_fin': 'Hora de fin',
            'asistentes': 'Número de asistentes',
            'salas': 'Salas solicitadas',
            'requerimientos': 'Requerimientos',
            'acomodo_sillas': 'Acomodo de sillas',
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['salas'].queryset = Sala.objects.filter(activa=True).order_by('orden')
        self.fields['requerimientos'].queryset = Requerimiento.objects.order_by('nombre')
        self.fields['requerimientos'].required = False
        self.fields['observaciones'].required = False
        self.fields['hora_inicio'].widget.choices = HORARIOS_RESERVA[:-1]
        self.fields['hora_fin'].widget.choices = HORARIOS_RESERVA[1:]

    def clean(self):
        cleaned_data = super().clean()
        fecha_evento = cleaned_data.get('fecha_evento')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        asistentes = cleaned_data.get('asistentes')
        salas = cleaned_data.get('salas')

        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')

        if hora_inicio and hora_inicio.minute != 0:
            raise forms.ValidationError('La hora de inicio debe seleccionarse en bloques exactos de una hora.')

        if hora_fin and hora_fin.minute != 0:
            raise forms.ValidationError('La hora de fin debe seleccionarse en bloques exactos de una hora.')

        if hora_inicio and hora_fin:
            duracion_horas = hora_fin.hour - hora_inicio.hour
            if duracion_horas < 1:
                raise forms.ValidationError('La reservación debe durar al menos una hora completa.')

        if asistentes and salas:
            capacidad_total = sum(sala.capacidad for sala in salas)

            if capacidad_total < asistentes:
                raise forms.ValidationError(
                    f'La capacidad de las salas seleccionadas es insuficiente. '
                    f'Capacidad total: {capacidad_total}. '
                    f'Asistentes registrados: {asistentes}. '
                    f'Selecciona más salas o una sala con mayor capacidad.'
                )

        if fecha_evento and hora_inicio and hora_fin and salas:
            reservaciones_empalmadas = Reservacion.objects.filter(
                fecha_evento=fecha_evento,
                estatus__in=['PENDIENTE', 'CONFIRMADA'],
                salas__in=salas,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio,
            ).distinct()

            if self.instance and self.instance.pk:
                reservaciones_empalmadas = reservaciones_empalmadas.exclude(pk=self.instance.pk)

            if reservaciones_empalmadas.exists():
                salas_ocupadas = []

                for reservacion in reservaciones_empalmadas:
                    for sala in reservacion.salas.filter(id__in=salas):
                        salas_ocupadas.append(sala.nombre)

                salas_ocupadas = sorted(set(salas_ocupadas))

                raise forms.ValidationError(
                    f'No se puede hacer la reservación. '
                    f'Las siguientes salas ya están ocupadas en ese horario: '
                    f'{", ".join(salas_ocupadas)}.'
                )

        return cleaned_data
