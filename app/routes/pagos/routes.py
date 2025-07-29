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
        SELECT * FROM detalles_pagos 
        WHERE (clave_participante ILIKE %s OR nombre_participante ILIKE %s) 
        ORDER BY id_pago DESC 
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
                           concepto=lista_conceptos(),
                           gasto=lista_gastos(),
                           search_query=search_query)

@pagos.route("/pagos/filtros")
@login_required
def pagos_filtros():
    mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # -------------------- PAGOS --------------------
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
        [mes, mes, semana, semana],
        page, per_page
    )

    # -------------------- GASTOS --------------------
    sql_countG = '''
        SELECT COUNT(*) FROM detalles_gastos
        WHERE (%s = '' OR mes ILIKE %s)
        AND (%s = '' OR semana ILIKE %s)
    '''

    sql_limG = '''
        SELECT * FROM detalles_gastos
        WHERE (%s = '' OR mes ILIKE %s)
        AND (%s = '' OR semana ILIKE %s)
        ORDER BY fecha DESC
        LIMIT %s OFFSET %s
    '''

    # Ejecutar paginador con los valores adecuados
    paginado_gastos = paginador3(
        sql_countG, sql_limG,
        [
         mes, mes, 
         semana, semana
        ],
        1, 10
    )

    # Renderizar plantilla
    return render_template('pagos/pagos.html',
                        pagos=paginado[0],
                        page=paginado[1],
                        per_page=paginado[2],
                        total_items=paginado[3],
                        total_pages=paginado[4],
                        gastos=paginado_gastos[0],
                        concepto=lista_conceptos(),
                        gasto=lista_gastos(),
                        meses=lista_meses(),
                        semanas=lista_semanas())

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

# ----------------------------------------AGREGAR----------------------------------------
@pagos.route("/pagos/agregar/gasto", methods = ("GET", "POST"))
@login_required
def pagos_nuevo():
    if request.method == 'POST':
        mes_filtro = request.form['mes_filtro']
        semana_filtro = request.form['semana_filtro']
        monto_gasto = request.form['gasto']
        concepto_gasto = request.form['conceptos']
        mes = request.form['mes']
        semana = request.form['semana']
        fecha = datetime.now().date()

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        sql = '''
                    INSERT INTO gastos
                        (fecha, monto_gasto, concepto_gasto, mes, semana)
                        VALUES (%s, %s, %s, %s, %s)
              '''
        valores = (fecha, monto_gasto, concepto_gasto, mes, semana)
        cur.execute(sql, valores)

        con.commit()
        cur.close()
        con.close()

        flash("Gasto registrado correctamente.")
        return redirect(url_for('pagos.pagos_filtros', mes = mes_filtro, semana = semana_filtro))
    
    return redirect(url_for('pagos.pagos_buscar'))

#-----------------------------------------AGREGAR FACTURA-----------------------------------------
@pagos.route("/pagos/agregar/factura/<string:id>", methods=["POST"])
@login_required
def factura_nueva(id):
    if request.method == 'POST':
        ingreso_factura = request.form['ingreso_factura']
        concepto_factura = request.form['conceptos']

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
