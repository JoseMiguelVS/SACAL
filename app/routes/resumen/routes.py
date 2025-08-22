from flask import Blueprint, flash, render_template, request
from flask_login import login_required
from datetime import datetime, timedelta, date
from psycopg2.extras import RealDictCursor
from collections import defaultdict
from ..utils.utils import get_db_connection, rol_admin_required
from app.utils.listas import lista_categorias, lista_meses
from collections import defaultdict
from decimal import Decimal
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
    def safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

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

    cur.execute("SELECT * FROM asistencias_detalladas")
    asistencias = cur.fetchall()

    cur.execute("SELECT * FROM detalles_pagos")
    pagos = cur.fetchall()

    cur.execute("SELECT * FROM detalles_gastos")
    gastos = cur.fetchall()

    cur.close()
    conn.close()

    # Inicialización segura del resumen
    resumen_datos = defaultdict(lambda: {
        "total_promesas": 0,
        "total_pagados": 0,
        "total_generado": 0.0,
        "iva": 0.0,
        "gastos": 0.0,
        "publicidad": 0.0,
        "gasto_ponente": 0.0,
        "honorarios": 0.0,
        "gastos_ventas": 0.0,
        "gastos_admin": 0.0,
        "nombre_ponente": set(),
        "nombre_curso": set(),
        "nombre_categoria": set(),
        "precio_paquete": 0.0
    })

    # Procesar asistencias
    for a in asistencias:
        fecha = a['fecha']
        if fecha_inicio and fecha < fecha_inicio.date():
            continue
        if fecha_fin and fecha > fecha_fin.date():
            continue

        resumen = resumen_datos[fecha]
        resumen["nombre_ponente"].update(str(x).strip() for x in a.get('ponentes', '').split(",") if x)
        resumen["nombre_curso"].update(str(x).strip() for x in a.get('cursos', '').split(",") if x)
        resumen["nombre_categoria"].add(str(a.get('nombre_categoria', '')).strip())
        resumen["precio_paquete"] = safe_float(a.get('precio_paquete'))
        resumen["precio_paquete"] = safe_float(a.get('precio_paquete'))

        # Procesar pagos
    for p in pagos:
        fecha = p['fecha_pago']
        if fecha_inicio and fecha < fecha_inicio.date():
            continue
        if fecha_fin and fecha > fecha_fin.date():
            continue

        resumen = resumen_datos[fecha]
        ingresos = safe_float(p.get('ingresos'))
        iva_valor = safe_float(p.get('iva'))

        resumen["total_pagados"] += int(ingresos > 0)
        resumen["total_promesas"] += int(ingresos == 0)
        resumen["total_generado"] += ingresos
        resumen["iva"] += ingresos * iva_valor

    # Procesar gastos
    for g in gastos:
        fecha = g['fecha']
        if fecha_inicio and fecha < fecha_inicio.date():
            continue
        if fecha_fin and fecha > fecha_fin.date():
            continue

        resumen = resumen_datos[fecha]
        monto = safe_float(g.get('monto_gasto'))
        concepto = g.get('nombre_gasto', '').lower()

        resumen["gastos"] += monto
        if "publicidad" in concepto:
            resumen["publicidad"] += monto
        elif "sueldos" in concepto:
            resumen["gasto_ponente"] += monto
        elif "honorarios" in concepto:
            resumen["honorarios"] += monto
        elif "ventas" in concepto:
            resumen["gastos_ventas"] += monto
        elif "administrativos" in concepto:
            resumen["gastos_admin"] += monto

    # Convertir sets a texto y calcular diferencia
    datos_finales = []
    for fecha, datos in resumen_datos.items():
        datos["fecha"] = fecha
        datos["nombre_ponente"] = ", ".join(sorted(datos["nombre_ponente"]))
        datos["nombre_curso"] = ", ".join(sorted(datos["nombre_curso"]))
        datos["nombre_categoria"] = ", ".join(sorted(datos["nombre_categoria"]))
        datos["diferencia"] = round(
            datos["total_generado"]
            - datos["gastos_ventas"]
            - datos["gastos_admin"]
            - datos["iva"],
            2
        )
        datos_finales.append(datos)

    datos_finales.sort(key=lambda x: x["fecha"], reverse=True)

    for fila in datos_finales:
        fecha = fila['fecha']
        fila['nombre_mes'] = fecha.strftime('%B').capitalize()
        fila['fecha_obj'] = fecha

    agrupado = defaultdict(list)
    for fila in datos_finales:
        clave = f"{fila['fecha']}_{fila['nombre_ponente']}_{fila['nombre_curso']}"
        agrupado[clave].append(fila)

    suma_total = sum(f['total_generado'] for f in datos_finales)
    publicidad_total = sum(f['publicidad'] for f in datos_finales)
    honorarios = sum(f['honorarios'] for f in datos_finales)
    gasto_total = sum(f['gastos'] for f in datos_finales)
    iva = sum(f['iva'] for f in datos_finales)
    sueldos = sum(f['gasto_ponente'] for f in datos_finales)

    total_gastos = publicidad_total + honorarios + iva + sueldos
    meta = 100000.0
    porcentaje = (suma_total / meta) * 100 if meta > 0 else 0
    ingreso_faltante = meta - suma_total if suma_total < meta else 0

    return render_template(
        'resumen/resumen.html',
        datos=datos_finales,
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
