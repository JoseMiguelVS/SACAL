from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from utils.listas import lista_meses, lista_semanas

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

    return render_template(
        'resumen/resumen.html',
        datos=resumen_datos,
        agrupado=agrupado,
        mes=mes,
        semana=semana,
        semanas = lista_semanas(),
        meses = lista_meses()
    )
