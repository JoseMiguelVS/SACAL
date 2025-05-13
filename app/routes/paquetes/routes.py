from flask import Blueprint, render_template, request, redirect, url_for, flash, Flask,make_response
from flask_login import login_required, current_user
from datetime import datetime
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

from ..utils.utils import get_db_connection, paginador2, allowed_paquename

paquetes = Blueprint('paquete', __name__)

#----------------------------------CONSULTA DE CATEGORIAS
def lista_categorias():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM categorias ORDER BY id_categoria ASC')
    categoria = cur.fetchall()
    cur.close()
    con.close()
    return categoria

#-------------------------BUSCAR PAQUETES / CONSULTA-----------------------
@paquetes.route("/paquetes")
@login_required
def paquetes_buscar():
    search_query = request.args.get('buscar', '', type = str).strip()

    if search_query:
        sql_count = 'SELECT COUNT(*) detalles_paquetes WHERE estado = True ADN nombre_paquete ILIKE %s;'
        sql_lim = 'SELECT * FROM detalles_paquetes WHERE estado = True AND nombre_paquete ILIKE %s ORDER BY id_paquete DESC LIMIT %s OFFSET;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT(*) FROM paquetes WHERE estado = True;'
        sql_lim = 'SELECT * FROM paquetes WHERE estado = True ORDER BY id_paquete DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1 , 5)

    return render_template('paquetes/paquetes.html',
                           paquetes=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)

#------------------------AGREGAR PAQUETE---------------------------
@paquetes.route("/paquetes/agregar")
@login_required
def paquete_agregar():
    titulo = "Agregar paquete"
    return render_template('paquetes/paquetes_agregar.html', titulo = titulo, categoria = lista_categorias())


@paquetes.route("/paquetes/agregar/nuevo", methods = ('GET', 'POST'))
@login_required
def paquete_nuevo():
    if request.method == 'POST':
        nombre_paquete = request.form['nombre_paquete']
        if allowed_paquename(nombre_paquete):
            precio_paquete = request.form['precio_paquete']
            categoria_paquete = request.form['id_categoria']
            estado = True
            fecha_creacion= datetime.now()
            fecha_modificacion = datetime.now()
            
            con = get_db_connection()
            cur = con.cursor(cursor_factory=RealDictCursor)
            sql_validar = 'SELECT COUNT(*) paquetes WHERE nombre_paquete = %s;'
            cur.execute(sql_validar, (nombre_paquete,))
            existe = cur.fetchone()['count']
            if existe:
                cur.close()
                con.close()
                flash('Error: El nombre seleccionado ya esta registrado. Intente con uno diferente')
                return redirect(url_for('paquetes.paquete_agregar'))
            else:
                sql = 'INSERT INTO paquetes (nombre_paquete, precio_paquete, categoria_paquete, estado, fecha_creacion, fecha_modificacion) VALUES (%s, %s, %s, %s, %s, %s)'
                valores = (nombre_paquete, precio_paquete, categoria_paquete, estado, fecha_creacion, fecha_modificacion)
                cur.execute(sql, valores)
                con.commit()
                cur.close()
                con.close()
                flash('Paquete agregado conrrectamente')
                return redirect(url_for('paquetes.paquetes_buscar'))
        else:
            flash('Error')
            return redirect(url_for('paquetes.paquete_agregar'))
    return redirect(url_for('paquetes.paquete_agregar'))

#---------------------------------------DETALLES DE PAQUETE------------------------------
@paquetes.route('/paquetes/detalles/<int:id>')
@login_required
def paquete_detalles(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM paquetes WHERE id_paquete = %s', (id))
            paquete = cur.fetchone()
    if paquete is None:
        flash('El paquete no existe o ha sido eliminado.')
        return redirect(url_for('paquetes.paquete_buscar'))
    return render_template('paquetes/paquete_detalles.html', paquete = paquete)

#------------------------------EDITAR PAQUETE---------------------------
@paquetes.route('/paquetes/editar/<string:id>')
@login_required
def paquete_editar(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM paquetes WHERE id_paquete = {0}'.format(id))
    paquete = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('/paquetes/paquete_editar.html', paquete = paquete[0], categoria = lista_categorias())

@paquetes.route('/paquetes/editar/<string:id>', methods = ['POST'])
@login_required
def paquete_actualizar(id):
    if request.method == 'POST':
        nombre_paquete = request.form['nombre_paquete']
        precio_paquete = request.form['precio_paquete']
        categoria_paquete = request.form['categoria_paquete']
        fecha_modificacion = datetime.now()

        con = get_db_connection()
        cur = con.cursor()
        sql = 'UPDATE paquetes SET nombre_paquete = %s, precio_paquete = %s, categoria_paquete = %s, fecha_modificacion = %s WHERE id_paquete = %s;'
        valores = (nombre_paquete, precio_paquete, categoria_paquete, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash('Paquete actualizado correctamente')
    return redirect(url_for('paquetes.paquetes_buscar'))

#-------------------------------ELIMINAR PAQUETES----------------------------
@paquetes.route('/paquetes/eliminar/<string:id>')
@login_required
def paquete_eliminar(id):
    estado = False
    fecha_modificacion = datetime.now()
    con = get_db_connection()
    cur = con.cursor()
    sql = 'UPDATE paquetes SET estado = %s, fecha_modificacion = %s WHERE id_paquete = %s;'
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql,valores)
    con.commit()
    cur.close()
    con.close()
    flash('Paquete eliminado correctamente')
    return redirect(url_for('paquetes.paquetes_buscar'))

#-------------------------PAPELERA DE PAQUETES--------------------------
@paquetes.route("/paquetes/papelera")
@login_required
def paquetes_papelera():
    search_query = request.args.get('buscar', '', type = str).strip()

    if search_query:
        sql_count = 'SELECT COUNT(*) detalles_paquetes WHERE estado = False ADN nombre_paquete ILIKE %s;'
        sql_lim = 'SELECT * FROM detalles_paquetes WHERE estado = False AND nombre_paquete ILIKE %s ORDER BY id_paquete DESC LIMIT %s OFFSET;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT(*) FROM detalles_paquetes WHERE estado = False;'
        sql_lim = 'SELECT * FROM detalles_paquetes WHERE estado = False ORDER BY id_paquete DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1 , 5)

    return render_template('paquetes/paquetes_papelera.html',
                           paquetes=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)

#----------------------------------DETALLES DE PAQUETES ELIMINADO-----------------------------
@paquetes.route('/paquetes/papelera/detalles/<int:id>')
@login_required
def paquete_detallesPapelera(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM paquetes WHERE id_paquete = %s', (id))
            paquete = cur.fetchone()
    if paquete is None:
        flash('El paquete no existe o ha sido eliminado.')
        return redirect(url_for('paquetes.paquete_buscar'))
    return render_template('paquetes/paquete_detallesPapelera.html', paquete = paquete)

#------------------------------------RESTAURAR PAQUETE ------------------------------
@paquetes.route('/paquetes/papelera/restaurar/<string:id>')
@login_required
def paquete_restaurar(id):
    estado = True
    fecha_modificacion = datetime.now()
    con = get_db_connection()
    cur = con.cursor()
    sql = 'UPDATE paquetes SET estado = %s, fecha_modificacion = %s WHERE id_paquete = %s;'
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql,valores)
    con.commit()
    cur.close()
    con.close()
    flash('Paquete restaurado correctamente')
    return redirect(url_for('paquetes.paquetes_buscar'))