from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from utils.listas import lista_cuentas, lista_cursos, lista_paquetes, lista_sesiones

from ..utils.utils import get_db_connection, paginador3

constancias = Blueprint('constancias', __name__)

@constancias.route("/constancias")
@login_required
def constancias_buscar():
    nombre_curso = request.args.get('nombre_curso', '', type=str)
    sesion = request.args.get('sesion', '', type=str)

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas
                   WHERE (%s = '' OR nombre_curso::text = %s)
                     AND (%s = '' OR fecha ILIKE %s)'''

    sql_lim = '''SELECT * FROM asistencias_detalladas
                 WHERE (%s = '' OR nombre_curso::text = %s)
                   AND (%s = '' OR fecha ILIKE %s)
                 ORDER BY nombre_participante DESC
                 LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [nombre_curso, nombre_curso, sesion, sesion],
        1, 5
    )

    return render_template('constancias/constancias.html',
                           cursos=lista_cursos(),
                           sesiones = lista_sesiones(),
                           paquetes = lista_paquetes(),
                           cuentas = lista_cuentas(),
                           constancias=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4])

@constancias.route("/constancias/detalles/<ind:id>")
@login_required
def constancias_detalles(id):
     with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM')