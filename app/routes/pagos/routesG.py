from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from app.utils.listas import lista_conceptos, lista_gastos

from ..utils.utils import get_db_connection, paginador3

from .routes import pagos

@pagos.route("/pagos/gastos")
@login_required
def gastos_filtros():
    fecha_inicio = request.args.get('fecha_inicio', '', type=str)
    fecha_fin = request.args.get('fecha_fin', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
     # -------------------- GASTOS --------------------
    sql_countG = '''
        SELECT COUNT(*) FROM detalles_gastos
        WHERE (%s = '' OR fecha >= %s)
        AND (%s = '' OR fecha <= %s)
    '''

    sql_limG = '''
        SELECT * FROM detalles_gastos
        WHERE (%s = '' OR fecha >= %s)
        AND (%s = '' OR fecha <= %s)
        ORDER BY fecha DESC
        LIMIT %s OFFSET %s
    '''

    paginado = paginador3(
        sql_countG, sql_limG,
        [fecha_inicio, fecha_inicio, fecha_fin, fecha_fin],
        page, per_page
    )
    
    return render_template(
        'pagos/gastos.html',
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        gastos=paginado[0],
        page=paginado[1],
        per_page=paginado[2],
        total_items=paginado[3],
        total_pages=paginado[4],
        conceptos=lista_conceptos(),
        gasto=lista_gastos()
    )

   # ----------------------------------------AGREGAR----------------------------------------
@pagos.route("/pagos/gasto/agregar", methods = ("GET", "POST"))
@login_required
def gastos_nuevo():
    if request.method == 'POST':
        monto_gasto = request.form['gasto']
        concepto_gasto = request.form['conceptos']
        fecha = datetime.now().date()

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        sql = '''
                    INSERT INTO gastos
                        (fecha, monto_gasto, concepto_gasto)
                        VALUES (%s, %s, %s)
              '''
        valores = (fecha, monto_gasto, concepto_gasto)
        cur.execute(sql, valores)

        con.commit()
        cur.close()
        con.close()

        flash("Gasto registrado correctamente.")
        return redirect(url_for('pagos.gastos_filtros'))
    
    return redirect(url_for('pagos.gastos_filtros'))