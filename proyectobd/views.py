from calendar import Calendar
from datetime import date, timedelta, time

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .forms import ReservacionForm
from .models import Reservacion, HistorialReservacion


MESES_ES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]


@login_required
def crear_reservacion(request):
    if request.method == 'POST':
        form = ReservacionForm(request.POST)

        if form.is_valid():
            reservacion = form.save(commit=False)
            reservacion.usuario = request.user
            reservacion.estatus = 'PENDIENTE'
            reservacion.save()
            form.save_m2m()

            HistorialReservacion.objects.create(
                reservacion=reservacion,
                usuario=request.user,
                accion='CREACION',
                descripcion='Reservación creada por el usuario.'
            )

            messages.success(request, 'La reservación se registró correctamente.')
            return redirect('lista_reservaciones')
    else:
        form = ReservacionForm()

    return render(request, 'proyectobd/crear_reservacion.html', {
        'form': form
    })


@login_required
def lista_reservaciones(request):
    Reservacion.finalizar_reservaciones_vencidas()

    reservaciones = Reservacion.objects.all().order_by('-fecha_evento', '-hora_inicio')

    hoy = timezone.localdate()
    semana_param = request.GET.get('week')

    try:
        anio = int(request.GET.get('year', hoy.year))
        mes = int(request.GET.get('month', hoy.month))
    except (TypeError, ValueError):
        anio, mes = hoy.year, hoy.month

    # Si la navegación se sale de [1, 12], pasamos al año siguiente/anterior
    if mes < 1:
        mes = 12
        anio -= 1
    elif mes > 12:
        mes = 1
        anio += 1

    primer_dia_mes = date(anio, mes, 1)
    mes_anterior = primer_dia_mes - timedelta(days=1)
    if mes == 12:
        primer_dia_siguiente = date(anio + 1, 1, 1)
    else:
        primer_dia_siguiente = date(anio, mes + 1, 1)
    mes_siguiente = primer_dia_siguiente

    reservaciones_mes = Reservacion.objects.filter(
        fecha_evento__year=anio,
        fecha_evento__month=mes,
    ).order_by('hora_inicio')

    if semana_param:
        try:
            fecha_base_semana = date.fromisoformat(semana_param)
        except ValueError:
            fecha_base_semana = hoy
    else:
        fecha_base_semana = hoy

    inicio_semana = fecha_base_semana - timedelta(days=fecha_base_semana.weekday())
    fin_semana = inicio_semana + timedelta(days=4)
    semana_anterior = inicio_semana - timedelta(days=7)
    semana_siguiente = inicio_semana + timedelta(days=7)

    horas_semana = [time(hora, 0) for hora in range(8, 20)]
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(5)]

    reservaciones_semana = Reservacion.objects.filter(
        fecha_evento__range=(inicio_semana, fin_semana),
    ).order_by('fecha_evento', 'hora_inicio')

    calendario_semanal = []

    for hora_bloque in horas_semana:
        fila = {
            'hora': hora_bloque,
            'dias': []
        }

        for dia_semana in dias_semana:
            eventos_bloque = []

            for reservacion in reservaciones_semana:
                if (
                    reservacion.fecha_evento == dia_semana
                    and reservacion.hora_inicio <= hora_bloque
                    and reservacion.hora_fin > hora_bloque
                ):
                    eventos_bloque.append(reservacion)

            fila['dias'].append({
                'fecha': dia_semana,
                'reservaciones': eventos_bloque,
            })

        calendario_semanal.append(fila)

    reservaciones_por_dia = {}
    for r in reservaciones_mes:
        reservaciones_por_dia.setdefault(r.fecha_evento.day, []).append(r)

    calendario = Calendar(firstweekday=0)  # semana inicia en lunes
    semanas = []
    semana_actual = []

    for dia in calendario.itermonthdates(anio, mes):
        semana_actual.append({
            'fecha': dia,
            'dia': dia.day,
            'es_mes_actual': dia.month == mes,
            'es_hoy': dia == hoy,
            'reservaciones': reservaciones_por_dia.get(dia.day, []) if dia.month == mes else [],
        })

        if len(semana_actual) == 7:
            semanas.append(semana_actual)
            semana_actual = []

    return render(request, 'proyectobd/lista_reservaciones.html', {
        'reservaciones': reservaciones,
        'semanas': semanas,
        'nombre_mes': MESES_ES[mes - 1],
        'anio': anio,
        'mes': mes,
        'mes_anterior': mes_anterior,
        'mes_siguiente': mes_siguiente,
        'hoy': hoy,
        'inicio_semana': inicio_semana,
        'fin_semana': fin_semana,
        'dias_semana': dias_semana,
        'calendario_semanal': calendario_semanal,
        'semana_anterior': semana_anterior,
        'semana_siguiente': semana_siguiente,
    })


@login_required
def detalle_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(Reservacion, id=reservacion_id)

    return render(request, 'proyectobd/detalle_reservacion.html', {
        'reservacion': reservacion
    })


@login_required
def confirmar_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(Reservacion, id=reservacion_id)

    if request.method == 'POST':
        reservacion.estatus = 'CONFIRMADA'
        reservacion.save()

        HistorialReservacion.objects.create(
            reservacion=reservacion,
            usuario=request.user,
            accion='CONFIRMACION',
            descripcion='Reservación confirmada.'
        )

        messages.success(request, 'La reservación fue confirmada correctamente.')

    return redirect('detalle_reservacion', reservacion_id=reservacion.id)


@login_required
def cancelar_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(Reservacion, id=reservacion_id)

    if request.method == 'POST':
        reservacion.estatus = 'CANCELADA'
        reservacion.save()

        HistorialReservacion.objects.create(
            reservacion=reservacion,
            usuario=request.user,
            accion='CANCELACION',
            descripcion='Reservación cancelada.'
        )

        messages.success(request, 'La reservación fue cancelada correctamente.')

    return redirect('detalle_reservacion', reservacion_id=reservacion.id)


@login_required
def finalizar_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(Reservacion, id=reservacion_id)

    if request.method == 'POST':
        reservacion.estatus = 'FINALIZADA'
        reservacion.save()

        HistorialReservacion.objects.create(
            reservacion=reservacion,
            usuario=request.user,
            accion='FINALIZACION',
            descripcion='Reservación finalizada.'
        )

        messages.success(request, 'La reservación fue finalizada correctamente.')

    return redirect('detalle_reservacion', reservacion_id=reservacion.id)


@login_required
def editar_reservacion(request, reservacion_id):
    reservacion = get_object_or_404(Reservacion, id=reservacion_id)

    if request.method == 'POST':
        form = ReservacionForm(request.POST, instance=reservacion)

        if form.is_valid():
            reservacion = form.save()

            HistorialReservacion.objects.create(
                reservacion=reservacion,
                usuario=request.user,
                accion='EDICION',
                descripcion='Reservación editada por el administrador.'
            )

            messages.success(request, 'La reservación fue actualizada correctamente.')
            return redirect('detalle_reservacion', reservacion_id=reservacion.id)
    else:
        form = ReservacionForm(instance=reservacion)

    return render(request, 'proyectobd/editar_reservacion.html', {
        'form': form,
        'reservacion': reservacion
    })