from flask import Blueprint, flash, render_template, request
from flask_login import login_required
from datetime import datetime, timedelta, date
from psycopg2.extras import RealDictCursor
from collections import defaultdict
from ..utils.utils import get_db_connection, rol_admin_required
from app.utils.listas import lista_categorias, lista_meses

resumen_semanal = Blueprint('resumen_semanal', __name__)

def lista_semanas(year=None):
    if year is None:
        year = date.today().year
    d = date(year, 1, 1)
    d -= timedelta(days=d.weekday())  # lunes igual o anterior al 1ro enero
    semanas = []
    semana_id = 1
    while d.year <= year:
        inicio = d
        fin = d + timedelta(days=6)
        if inicio.year > year:
            break
        texto = f"{inicio.day:02d} {inicio.strftime('%b')} - {fin.day:02d} {fin.strftime('%b')}"
        semanas.append((semana_id, texto))
        semana_id += 1
        d += timedelta(weeks=1)
    return semanas

@resumen_semanal.route('/resumen', methods=['GET'])
@login_required
@rol_admin_required
def resumen():
    fecha_inicio_str = request.args.get('fecha_inicio', '', type=str)
    fecha_fin_str = request.args.get('fecha_fin', '', type=str)

    fecha_inicio = None
    fecha_fin = None

    try:
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
    except ValueError:
        flash("Fechas inválidas", "warning")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Armar la consulta dinámica
    sql = "SELECT * FROM resumen_semanal"
    condiciones = []
    valores = []

    if fecha_inicio:
        condiciones.append("fecha >= %s")
        valores.append(fecha_inicio)

    if fecha_fin:
        condiciones.append("fecha <= %s")
        valores.append(fecha_fin)

    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)

    sql += " ORDER BY fecha DESC"

    cur.execute(sql, tuple(valores))
    resumen_datos = cur.fetchall()
    cur.close()
    conn.close()

    # Procesar datos
    for fila in resumen_datos:
        fecha_str = fila.get('fecha')
        if fecha_str:
            fecha = datetime.strptime(str(fecha_str), "%Y-%m-%d")
            fila['nombre_mes'] = fecha.strftime('%B').capitalize()
            fila['fecha_obj'] = fecha
        else:
            fila['nombre_mes'] = ''
            fila['fecha_obj'] = None

    # Agrupar por fecha, ponente y curso
    agrupado = defaultdict(list)
    for fila in resumen_datos:
        clave = f"{fila['fecha']}_{fila['nombre_ponente']}_{fila['nombre_curso']}"
        agrupado[clave].append(fila)

    # Calcular totales
    suma_total = sum(float(fila.get('total_generado') or 0) for fila in resumen_datos)
    publicidad_total = sum(float(fila.get('publicidad') or 0) for fila in resumen_datos)
    honorarios = sum(float(fila.get('honorarios') or 0) for fila in resumen_datos)
    gasto_total = sum(float(fila.get('gastos') or 0) for fila in resumen_datos)
    iva = sum(float(fila.get('iva') or 0) for fila in resumen_datos)
    sueldos = sum(float(fila.get('gasto_ponente') or 0) for fila in resumen_datos)

    total_gastos = publicidad_total + honorarios + iva + sueldos
    meta = 100000.0
    porcentaje = (suma_total / meta) * 100 if meta > 0 else 0
    ingreso_faltante = meta - suma_total if suma_total < meta else 0

    return render_template(
        'resumen/resumen.html',
        datos=resumen_datos,
        agrupado=agrupado,
        fecha_inicio=fecha_inicio_str,
        fecha_fin=fecha_fin_str,
        categorias=lista_categorias(),
        meses=lista_meses(),
        suma_total=suma_total,
        publicidad_total=publicidad_total,
        honorarios=honorarios,
        iva=iva,
        sueldos=sueldos,
        total_gastos=total_gastos,
        meta=meta,
        porcentaje=porcentaje,
        ingreso_faltante=ingreso_faltante,
        gasto_semanal=gasto_total
    )
