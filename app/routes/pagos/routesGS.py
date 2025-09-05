from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from app.utils.listas import lista_meses, lista_semanas

from ..utils.utils import get_db_connection, paginador3

from .routes import pagos

@pagos.route("/pagos/gastos_sesiones")
@login_required
def gastos_sesiones_filtros():
    nombre_mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
     # -------------------- GASTOS DETALLADOS (vista) --------------------
    sql_countGD = '''
        SELECT COUNT(*) FROM vista_gastos_detallados
        WHERE (%s = '' OR nombre_mes ILIKE %s)
        AND (%s = '' OR semana ILIKE %s)
    '''

    sql_limGD = '''
        SELECT * FROM vista_gastos_detallados
        WHERE (%s = '' OR nombre_mes ILIKE %s)
        AND (%s = '' OR semana ILIKE %s)
        ORDER BY fecha_curso DESC
        LIMIT %s OFFSET %s
    '''

    paginado = paginador3(
        sql_countGD, sql_limGD,
        [ nombre_mes, nombre_mes, 
            semana, semana, ],
        page, per_page
    )
    return render_template(
        'pagos/gastos_sesiones.html',
        meses=lista_meses(),
        semanas=lista_semanas(),
        gastos_sesiones=paginado[0],
        page=paginado[1],
        per_page=paginado[2],
        total_items=paginado[3],
        total_pages=paginado[4]
    )
    #-----------------------------------------AGREGAR GASTOS DE SESIONES-----------------------------------------
@pagos.route("/pagos/gastos_sesiones/<string:id>", methods=['POST'])
@login_required
def gastos_sesiones(id):
    if request.method == 'POST':
        publicidad = request.form['gasto_publi']
        honorarios = request.form['gasto_hono']
        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        sql = '''
                    UPDATE gastos_sesiones
                        SET publicidad = %s, honorarios = %s
                        WHERE id_gasto_sesion = %s
              '''
        valores = (publicidad, honorarios, id)
        cur.execute(sql, valores)

        con.commit()
        cur.close()
        con.close()

        flash("Gasto registrado correctamente.")
        return redirect(url_for('pagos.gastos_sesiones_filtros'))
    
    return redirect(url_for('pagos.gastos_sesiones_filtros'))
