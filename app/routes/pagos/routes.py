from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from utils.listas import lista_meses, lista_semanas

from ..utils.utils import get_db_connection, paginador3

# Blueprint
pagos = Blueprint('pagos', __name__)

# ---------------------------------BUSCAR PAGOS---------------------------------
@pagos.route("/pagos")
@login_required
def pagos_buscar():
    search_query = request.args.get('buscar', '', type=str).strip()
    search_query_sql = f"%{search_query}%"

    sql_count = '''
        SELECT COUNT(*) FROM detalles_pagos 
        WHERE (clave_participante ILIKE %s OR nombre_participante ILIKE %s)
    '''

    sql_lim = '''
        SELECT * FROM detalles_pagos 
        WHERE (clave_participante ILIKE %s OR nombre_participante ILIKE %s) 
        ORDER BY id_pago DESC 
        LIMIT %s OFFSET %s
    '''

    paginado = paginador3(sql_count, sql_lim, [search_query_sql, search_query_sql], 1, 5)

    return render_template('pagos/pagos.html',
                           meses=lista_meses(),
                           semanas=lista_semanas(),
                           pagos=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)


@pagos.route("/pagos/filtros")
@login_required
def pagos_filtros():
    mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)

    sql_count = '''
                    SELECT COUNT(*) FROM detalles_pagos
                    WHERE (%s = '' OR meses ILIKE %s)
                    AND (%s = '' OR semanas ILIKE %s)
                '''
    
    sql_lim = '''
                    SELECT * FROM detalles_pagos
                    WHERE (%s = '' OR meses ILIKE %s)
                    AND (%s = '' OR semanas ILIKE %s)
                    ORDER BY id_pago DESC
                    LIMIT %s OFFSET %s
                '''
    paginado = paginador3(
        sql_count, sql_lim,
        [
            mes, mes,
            semana, semana
        ],
        1, 20
    )

    return render_template('pagos/pagos.html',
                           meses=lista_meses(),
                           semanas=lista_semanas(),
                           pagos=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4])

# -----------------------------COMPROBANTES-----------------------------
@pagos.route("/pagos/comprobantes/<string:id>")
@login_required
def pagos_comprobantes(id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM detalles_pagos2 WHERE id_participante = %s',(id,))
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

# -----------------------------------DETALLES DE PAGOS-----------------------------------
@pagos.route("/pagos/detalles/<int:id>")
@login_required
def pagos_detalles(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM detalles_pagos WHERE id_pago = %s', (id,))
            pago=cur.fetchone()
    if pago is None:
        flash('El pago no existe o ha sido eliminado.')
        return redirect(url_for('pagos.pagos_buscar'))
    return render_template('pagos/pagos_detalles.html', pago=pago)

# ----------------------------------------AGREGAR----------------------------------------
@pagos.route("/pagos/agregar/gasto", methods = ("GET", "POST"))
@login_required
def pagos_nuevo():
    if request.method == 'POST':
        gasto = request.form['gasto']
        conceptos = request.form['conceptos']
        ingresos = '0'
        clave_rastreo = 'N/A'
        fecha_pago = datetime.now()
        validacion_pago = '3'
        participante = '1'

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        sql = '''
                    INSERT INTO pagos
                        (gasto, ingresos, clave_rastreo, conceptos, fecha_pago,validacion_pago, participante)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
              '''
        valores = (gasto, ingresos, clave_rastreo, conceptos, fecha_pago,validacion_pago, participante)
        cur.execute(sql, valores)

        con.commit()
        cur.close()
        con.close()

        flash("Gasto registrado correctamente.")
        return redirect(url_for('pagos.pagos_buscar'))
    
    return redirect(url_for('pagos.pagos_buscar'))

@pagos.route("/pagos/agregar/factura/<string:id>", methods=["POST"])
@login_required
def factura_nueva(id):
    if request.method == 'POST':
        ingreso_factura = request.form['ingreso_factura']
        concepto_factura = request.form['conceptos_factura']

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        sql = '''
                    UPDATE pagos SET ingreso_factura = %s, concepto_factura =%s WHERE id_pago = %s
              '''
        cur.execute(sql,(ingreso_factura, concepto_factura, id))

        con.commit()
        cur.close()
        con.close()

        flash("Factura registrada con exito")
    return redirect(url_for("pagos.pagos_buscar"))
