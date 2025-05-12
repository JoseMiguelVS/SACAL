from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..utils.utils import get_db_connection, paginador1, allowed_pontname

#definir blueprint
ponentes = Blueprint('ponentes', __name__)

#-----------------------------------------BUSCAR PONENTE------------------------------------------------------

@ponentes.route("/ponentes")
@login_required
def ponentes_buscar():
    search_query = request.args.get('buscar', '', type = str)
    sql_count = 'SELECT COUNT(*) FROM ponentes WHERE estado = true AND (nombre_ponente ILIKE %s OR curp_ponente ILIKE %s);'
    sql_lim = 'SELECT * FROM ponentes WHERE estado = true AND (nombre_ponente ILIKE %s OR curp_ponente ILIKE %s) ORDER BY id_ponentes DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('ponentes/ponentes.html',
                           ponentes = paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query = search_query)

#-------------------------------------AGREGAR PONENTE----------------------------------
@ponentes.route('/ponentes/agregar')
@login_required
def ponente_agregar():
    titulo = ' Agregar ponente'
    return render_template('ponentes/ponentes_agregar.html', titulo = titulo)

@ponentes.route("/ponentes/agregar/nuevo", methods = ('GET','POST'))
@login_required
def ponente_nuevo():
    if request.method == 'POST':
        curp_ponente = request.form['curp_ponente']
        if allowed_pontname(curp_ponente):
            nombre_ponente = request.form['nombre_ponente']
            curp_ponente = request.form['curp_ponente']
            cedula_ponente = request.form['cedula_ponente']
            stps_ponente = request.form['stps_ponente']
            conocer_ponente = request.form['conocer_ponente']
            conocer2_ponente = request.form['conocer2_ponente']
            estado = True
            fecha_creacion= datetime.now()
            fecha_modificacion = datetime.now()

            conn = get_db_connection()
            cur = conn.cursor(cursor_factory = RealDictCursor)
            sql_validar = "SELECT COUNT(*) FROM ponentes WHERE curp_ponente = %s"
            cur.execute(sql_validar, (curp_ponente,))
            existe = cur.fetchone()['count']
            if existe:
                cur.close()
                conn.close()
                flash('Error: El curp del ponente ya se encuentra registrado. Intente con otro')
                return redirect(url_for('ponentes.ponente_agregar'))
            else:
                sql = 'INSERT INTO ponentes (nombre_ponente, curp_ponente, cedula_ponente, stps_ponente, conocer_ponente, conocer2_ponente, estado, fecha_creacion, fecha_modificacion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
                valores = (nombre_ponente, curp_ponente, cedula_ponente, stps_ponente, conocer_ponente, conocer2_ponente, estado, fecha_creacion, fecha_modificacion)
                cur.execute(sql,valores)
                conn.commit()
                cur.close()
                conn.close()
                flash('Ponente agregado correctamente')
                return redirect(url_for('ponentes.ponentes_buscar'))
        else:
            flash('Error: El curp no cuenta con las caracteristicas')
            return redirect(url_for('ponentes.ponente_agregar'))
    return redirect(url_for('ponentes.ponente_agregar'))

#------------------------------------DETALLES DE PONENTES----------------------------
@ponentes.route('/ponentes/detalles/<int:id>')
@login_required
def ponente_detalles(id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory = RealDictCursor) as cur:
            cur.execute('SELECT * FROM ponentes WHERE id_ponentes = %s',(id,))
            ponente = cur.fetchone()
    if ponente is None:
        flash('El ponente no existe o ha sido eliminado.')
        return redirect(url_for('ponentes.ponentes_buscar'))
    return render_template('ponentes/ponentes_detalles.html', ponente = ponente)

#------------------------------------EDITAR PONENTE----------------------------------
@ponentes.route('/ponentes/editar/<string:id>')
@login_required
def ponente_editar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM ponentes WHERE id_ponentes={0}'.format(id))
    ponente = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return render_template('ponentes/ponentes_editar.html', ponente = ponente[0])

@ponentes.route('/ponente/editar/<string:id>',methods=['POST'])
@login_required
def ponente_actualizar(id):
    if request.method == 'POST':
        nombre_ponente = request.form['nombre_ponente']
        curp_ponente = request.form['curp_ponente']
        cedula_ponente = request.form['cedula_ponente']
        stps_ponente = request.form['stps_ponente']
        conocer_ponente = request.form['conocer_ponente']
        conocer2_ponente = request.form['conocer2_ponente']
        fecha_modificacion = datetime.now()

        conn = get_db_connection()
        cur = conn.cursor()
        sql = "UPDATE ponentes SET nombre_ponente = %s, curp_ponente = %s, cedula_ponente = %s, stps_ponente = %s, conocer_ponente = %s, conocer2_ponente = %s, fecha_modificacion = %s WHERE id_ponentes = %s"
        valores = (nombre_ponente, curp_ponente, cedula_ponente, stps_ponente, conocer_ponente, conocer2_ponente, fecha_modificacion, id)
        cur.execute(sql,valores)
        conn.commit()
        cur.close()
        conn.close()
        flash("Ponente actualizado correctamente")
    return redirect(url_for('ponentes.ponentes_buscar'))

#*---------------------------------ELIMINAR PONENTE--------------------------------
@ponentes.route('/ponentes/eliminar/<string:id>')
@login_required
def ponente_eliminar(id):
    estado = False
    fecha_modificacion = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    sql = "UPDATE ponentes SET estado = %s,fecha_modificacion = %s WHERE id_ponentes = %s"
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql, valores)
    conn.commit()
    cur.close()
    conn.close()
    flash("Ponente eliminado correctamente")
    return redirect(url_for('ponentes.ponentes_buscar'))

#--------------------------------PAPELERA DE PONENTES--------------------------------

@ponentes.route('/ponentes/pepelera')
@login_required
def ponentes_papelera():
    search_query = request.args.get('buscar', '', type = str)
    sql_count = 'SELECT COUNT(*) FROM ponentes WHERE estado = false AND (nombre_ponente ILIKE %s OR curp_ponente ILIKE %s);'
    sql_lim = 'SELECT * FROM ponentes WHERE estado = false AND (nombre_ponente ILIKE %s OR curp_ponente ILIKE %s) ORDER BY id_ponentes DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count, sql_lim, search_query, 1, 5)
    return render_template('ponentes/ponentes_papelera.html',
                           ponentes = paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query = search_query)

#------------------------------------DETALLES DE PONENTES ELIMINADO-----------------------------
@ponentes.route('/ponentes/papelera/detalles/<int:id>')
@login_required
def ponente_detallesPapelera(id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM ponentes WHERE id_ponentes = %s',(id,))
            ponente = cur.fetchone()
    if ponente is None:
        flash('El ponente no existe o ah sido eliminado.')
        return redirect(url_for('ponentes.ponentes_buscar'))
    return render_template('ponentes/ponente_detallesPapelera.html', ponente = ponente)

#-------------------------------RESTAURAR PONENTE--------------------------
@ponentes.route('/ponentes/papelera/restaurar/<string:id>')
@login_required
def ponente_restaurar(id):
    estado = True
    fecha_modificacion = datetime.now()
    conn = get_db_connection()
    cur = conn.cursor()
    sql = "UPDATE ponentes SET estado = %s,fecha_modificacion = %s WHERE id_ponentes = %s"
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql, valores)
    conn.commit()
    cur.close()
    conn.close()
    flash("Ponente resturardo correctamente")
    return redirect(url_for('ponentes.ponentes_buscar'))
