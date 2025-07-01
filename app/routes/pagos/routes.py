from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..utils.utils import get_db_connection, paginador1

# Blueprint
pagos = Blueprint('pagos', __name__)

# ---------------------------------BUSCAR PAGOS---------------------------------
@pagos.route("/pagos")
@login_required
def pagos_buscar():
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM detalles_pagos WHERE (clave_participante ILIKE %s OR nombre_participante ILIKE %s);'
    sql_lim = 'SELECT * FROM detalles_pagos WHERE (clave_participante ILIKE %s OR nombre_participante ILIKE %s) ORDER BY id_pago DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('pagos/pagos.html',
                           pagos=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query = search_query)

# 
@pagos.route("/pagos/comprobantes/<string:id>")
@login_required
def pagos_comprobantes(id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM detalles_pagos WHERE id_participante = %s',(id,))
            pagos = cur.fetchone()
    if pagos is None:
        flash('El particiante no existe o ha sido eliminado.')
        return redirect(url_for('pagos.pagos_buscar'))
    return render_template('pagos/pagos_detalles.html', pagos = pagos)

@pagos.route("/pagos/comprobantes/editar/<string:id>", methods=['POST'])
@login_required
def pagos_actualizar(id):
    if request.method == 'POST':
        clave_rastreo = request.form['clave_rastreo']
        validacion_pago = request.form['validacion_pago']
        devolucion = request.form['devolucion']

        con = get_db_connection()
        cur = con.cursor()
        sql = 'UPDATE pagos SET clave_rastreo = %s, validacion_pago = %s WHERE participante = %s'
        valores = (clave_rastreo, validacion_pago, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash('Pago actualizado correctamente')
    return redirect(url_for('pagos.pagos_buscar'))