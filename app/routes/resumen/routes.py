from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from app.utils.listas import lista_categorias, lista_meses, lista_semanas

from ..utils.utils import get_db_connection, paginador3

from collections import defaultdict

resumen_semanal = Blueprint('resumen_semanal', __name__) 

#--------------------------------------------MAIN--------------------------------------------

@resumen_semanal.route('/resumen', methods=['GET'])
@login_required
def resumen():
    mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)

    mes_pattern = f"%{mes}%"
    semana_pattern = f"%{semana}%"

    sql = ''' 
            SELECT * FROM resumen_semanal
            WHERE (%s = '' OR nombre_mes ILIKE %s)
            AND (%s = '' OR semana ILIKE %s)
          '''

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql, (mes, mes_pattern, semana, semana_pattern))
    resumen_datos = cur.fetchall()
    cur.close()
    conn.close()

    # Resto igual
    from collections import defaultdict
    agrupado = defaultdict(list)
    for fila in resumen_datos:
        clave = f"{fila['semana']}_{fila['nombre_ponente']}_{fila['nombre_curso']}"
        agrupado[clave].append(fila)

        # Calcular totales
    suma_total = sum(float(fila['total_generado']) for fila in resumen_datos)
    publicidad_total = sum(float(fila['publicidad']) for fila in resumen_datos)
    honorarios = sum(float(fila['honorarios']) for fila in resumen_datos)
    gasto_semanal = sum(float(fila['gastos']) for fila in resumen_datos)
    iva = sum(float(fila['iva']) for fila in resumen_datos)

    # Si tienes columna 'sueldos', cámbiala; si no, puedes poner un valor fijo o quitarlo
    sueldos = sum(f.get("sueldos", 0) for f in resumen_datos)

    # Gasto total
    total_gastos = publicidad_total + honorarios + iva + sueldos

    # Meta y cálculo adicional
    meta = 100000.0
    porcentaje = (suma_total / meta) * 100 if meta > 0 else 0
    ingreso_faltante = meta - suma_total if suma_total < meta else 0


    return render_template(
    'resumen/resumen.html',
    datos=resumen_datos,
    agrupado=agrupado,
    mes=mes,
    semana=semana,
    categorias=lista_categorias(),
    semanas=lista_semanas(),
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
    gasto_semanal=gasto_semanal
)