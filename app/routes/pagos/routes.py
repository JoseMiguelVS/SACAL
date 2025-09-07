from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from app.utils.listas import lista_conceptos, lista_gastos, lista_meses, lista_semanas

from ..utils.utils import get_db_connection, paginador3

# Blueprint
pagos = Blueprint('pagos', __name__)

# ---------------------------------BUSCAR PAGOS---------------------------------
@pagos.route("/pagos")
@login_required
def pagos_buscar():
    # Búsqueda
    search_query = request.args.get('buscar', '', type=str).strip()
    search_query_sql = f"%{search_query}%"
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Pagos con búsqueda
    sql_count = '''
        SELECT COUNT(*) FROM detalles_pagos 
        WHERE (clave_participante ILIKE %s OR nombre_participante ILIKE %s)
    '''
    sql_lim = '''
        SELECT dp.*, pa.factura_pago
        FROM detalles_pagos dp
        JOIN participantes pa ON dp.clave_participante = pa.clave_participante
        WHERE (dp.clave_participante ILIKE %s OR dp.nombre_participante ILIKE %s)
        ORDER BY dp.id_pago DESC
        LIMIT %s OFFSET %s

    '''
    paginado = paginador3(sql_count, sql_lim, 
                          [
                              search_query_sql, search_query_sql
                          ], 
                          page, per_page)

    return render_template('pagos/pagos.html',
                           meses=lista_meses(),
                           semanas=lista_semanas(),
                           pagos=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           conceptos=lista_conceptos(),
                           gasto=lista_gastos(),
                           search_query=search_query)

@pagos.route("/pagos/filtros")
@login_required
def pagos_filtros():
    fecha_inicio = request.args.get('fecha_inicio', '', type=str)
    fecha_fin = request.args.get('fecha_fin', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # -------------------- PAGOS --------------------
    sql_count = '''
        SELECT COUNT(*) FROM detalles_pagos
        WHERE (%s = '' OR fecha_pago >= %s)
        AND (%s = '' OR fecha_pago <= %s)
    '''
    
    sql_lim = '''
        SELECT * FROM detalles_pagos
        WHERE (%s = '' OR fecha_pago >= %s)
        AND (%s = '' OR fecha_pago <= %s)
        ORDER BY id_pago DESC
        LIMIT %s OFFSET %s
    '''

    paginado = paginador3(
        sql_count, sql_lim,
        [fecha_inicio, fecha_inicio, fecha_fin, fecha_fin],
        page, per_page
    )

    return render_template(
        'pagos/pagos.html',
        paginado=paginado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        pagos=paginado[0],
        page=paginado[1],
        per_page=paginado[2],
        total_items=paginado[3],
        total_pages=paginado[4]
    )

# -----------------------------COMPROBANTES-----------------------------
@pagos.route("/pagos/comprobantes/<string:id>")
@login_required
def pagos_comprobantes(id):
    supabase_url="https://ipecmsarkhzdzkkanxvj.supabase.co/storage/v1/object/public/tickets"
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM detalles_pagos2 WHERE id_pago = %s',(id,))
            pagos = cur.fetchone()
    if pagos is None:
        flash('El particiante no existe o ha sido eliminado.')
        return redirect(url_for('pagos.pagos_buscar'))
    return render_template('pagos/pagos_detalles.html', pagos = pagos, url = supabase_url)

@pagos.route("/pagos/comprobantes/editar/<string:id>", methods=['POST'])
@login_required
def pagos_actualizar(id):
    if request.method == 'POST':
        clave_rastreo = request.form['clave_rastreo']
        validacion_pago = request.form['validacion_pago']
        ingresos = request.form['ingreso_real']

        con = get_db_connection()
        cur = con.cursor()
        sql = 'UPDATE pagos SET clave_rastreo = %s, validacion_pago = %s, ingresos = %s WHERE participante = %s'
        valores = (clave_rastreo, validacion_pago, ingresos, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash('Pago actualizado correctamente')
    return redirect(url_for('pagos.pagos_buscar'))

#----------------------------------------------DEVOLUCION----------------------------------------------
@pagos.route("/pagos/devolucion/<string:id>", methods=['POST'])
@login_required
def pagos_devolucion(id):
    devolucion = request.form.get('devolucion', '0')

    try:
        con = get_db_connection()
        cur = con.cursor()
        sql = '''
            UPDATE pagos
            SET ingresos = %s,
                ingreso_factura = %s,
                devolucion = %s
            WHERE id_pago = %s
        '''
        valores = (0, 0, devolucion, id)
        cur.execute(sql, valores)
        con.commit()
        flash('Devolución registrada correctamente', 'success')
    except Exception as e:
        flash(f'Error al registrar devolución: {e}', 'danger')
    finally:
        cur.close()
        con.close()

    return redirect(url_for('pagos.pagos_buscar'))

# -----------------------------------DETALLES DE PAGOS-----------------------------------
@pagos.route("/pagos/detalles/<int:id>")
@login_required
def pagos_detalles(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM detalles_pagos2 WHERE id_pago = %s', (id,))
            pago=cur.fetchone()
    if pago is None:
        flash('El pago no existe o ha sido eliminado.')
        return redirect(url_for('pagos.pagos_buscar'))
    return render_template('pagos/pagos_detalles.html', pagos=pago)

#-----------------------------------------AGREGAR FACTURA PAGOS-----------------------------------------
@pagos.route("/pagos/agregar/factura/<string:id>", methods=["POST"])
@login_required
def factura_nueva(id):
    if request.method == 'POST':
        ingreso_factura = request.form['ingreso_factura']
        concepto_factura = request.form['concepto_factura']

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        sql = '''
                    UPDATE pagos SET ingresos =%s, ingreso_factura = %s, concepto_factura =%s WHERE id_pago = %s
              '''
        cur.execute(sql,(0, ingreso_factura, concepto_factura, id))

        con.commit()
        cur.close()
        con.close()

        flash("Factura registrada con exito")
    return redirect(url_for("pagos.pagos_buscar"))
