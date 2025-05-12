from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..utils.utils import get_db_connection, paginador2, allowed_catname

#definir blueprint
categorias = Blueprint('categorias', __name__)

#--------------------------------------BUSCAR CATEGORIA-----------------------------------------
@categorias.route("/categorias")
@login_required
def categorias_buscar():
    search_query = request.args.get('buscar', '', type=str).strip()

    if search_query:
        sql_count = 'SELECT COUNT(*) FROM categorias WHERE estado = true AND nombre_categoria ILIKE %s;'
        sql_lim = 'SELECT * FROM categorias WHERE estado = true AND nombre_categoria ILIKE %s ORDER BY id_categoria DESC LIMIT %s OFFSET %s;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT(*) FROM categorias WHERE estado = true;'
        sql_lim = 'SELECT * FROM categorias WHERE estado = true ORDER BY id_categoria DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1, 5)

    return render_template('categorias/categorias.html',
                           categorias=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)


#------------------------------AGREGAR CATEGORIA--------------------------------
@categorias.route('/categorias/agregar')
@login_required
def categoria_agregar():
    titulo ='Agregar categoria'
    return render_template('categorias/categorias_agregar.html', titulo = titulo)

@categorias.route('/categorias/agregar/nuevo', methods = ('GET', 'POST'))
@login_required
def categoria_nuevo():
    if request.method == 'POST':
        nombre_categoria = request.form['nombre_categoria']
        if allowed_catname(nombre_categoria):
            nombre_categoria = request.form['nombre_categoria']
            estado = True
            fecha_creacion= datetime.now()
            fecha_modificacion = datetime.now()

            con = get_db_connection()
            cur = con.cursor(cursor_factory = RealDictCursor)
            sql_validar = "SELECT COUNT(*) FROM categorias WHERE nombre_categoria = %s"
            cur.execute(sql_validar, (nombre_categoria,))
            existe = cur.fetchone()['count']
            if existe:
                cur.close()
                con.close()
                flash('Error: la categoria ya se encuentra registrada')
                return redirect(url_for('categorias.categorias_buscar'))
            else:
                sql = 'INSERT INTO categorias(nombre_categoria, estado, fecha_creacion, fecha_modificacion) VALUES (%s,%s,%s,%s);'
                valores = (nombre_categoria, estado, fecha_creacion, fecha_modificacion)
                cur.execute(sql,valores)
                con.commit()
                cur.close()
                con.close()
                flash('Categoria agregada correctamente')
                return redirect(url_for('categorias.categorias_buscar'))
        else:
            flash ('Error')
            return redirect(url_for('categortias.categorias_agregar'))
    return redirect(url_for('categorias.categoria_agregar'))

#------------------------------------DETALLES DE CATEGORIAS------------------------
@categorias.route('/categorias/detalles/<int:id>')
@login_required
def categoria_detalles(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory = RealDictCursor) as cur:
            cur.execute('SELECT * FROM categorias WHERE id_categoria = %s',(id,))
            categoria = cur.fetchone()
    if categoria is None:
        flash('La categoria no existe o ah sido eliminada.')
        return redirect(url_for('categorias.categorias_buscar'))
    return render_template('categorias/categorias_detalles.html', categoria = categoria)

#----------------------------------EDITAR CATEGORIA -------------------------------
@categorias.route('/categorias/editar/<string:id>')
@login_required
def categoria_editar(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM categorias WHERE id_categoria ={0}'.format(id))
    categoria = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('categorias/categorias_editar.html', categoria = categoria[0])

@categorias.route('/categorias/editar/<string:id>', methods = ['POST'])
@login_required
def categoria_actualizar(id):
    if request.method == 'POST':
        nombre_categoria = request.form['nombre_categoria']
        fecha_modificacion = datetime.now()

        con = get_db_connection()
        cur = con.cursor()
        sql = "UPDATE categorias SET nombre_categoria = %s, fecha_modificacion = %s WHERE id_categoria = %s"
        valores = (nombre_categoria, fecha_modificacion, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash("Categoria actualizada correctamente")
    return redirect(url_for('categorias.categorias_buscar'))

#--------------------------------------ELIMINAR CATEGORIA-------------------------
@categorias.route('/categorias/eliminar/<string:id>')
@login_required
def categoria_eliminar(id):
    estado = False
    fecha_modificacion = datetime.now()
    con = get_db_connection()
    cur = con.cursor()
    sql = "UPDATE categorias SET estado = %s, fecha_modificacion = %s WHERE id_categoria = %s"
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql, valores)
    con.commit()
    cur.close()
    con.close()
    flash("categoria eliminada correctamente")
    return redirect(url_for('categorias.categorias_buscar'))

#-----------------------------------PAPELERA DE CATEGORIAS----------------------------
@categorias.route("/categorias/papelera")
@login_required
def categorias_papelera():
    search_query = request.args.get('buscar', '', type=str).strip()

    if search_query:
        sql_count = 'SELECT COUNT(*) FROM categorias WHERE estado = false AND nombre_categoria ILIKE %s;'
        sql_lim = 'SELECT * FROM categorias WHERE estado = false AND nombre_categoria ILIKE %s ORDER BY id_categoria DESC LIMIT %s OFFSET %s;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT(*) FROM categorias WHERE estado = false;'
        sql_lim = 'SELECT * FROM categorias WHERE estado = false ORDER BY id_categoria DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1, 5)

    return render_template('categorias/categorias_papelera.html',
                           categorias=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)

#------------------------------------DETALLES DE CATEGORIAS ELIMINADO------------------------
@categorias.route('/categorias/papelera/detalles/<int:id>')
@login_required
def categoria_detallesPapelera(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory = RealDictCursor) as cur:
            cur.execute('SELECT * FROM categorias WHERE id_categorias = %s',(id,))
            categoria =cur.fetchone()
    if categorias is None:
        flash('La categoria no existe o ah sido eliminada.')
        return redirect(url_for('categorias.categorias_buscar'))
    return render_template('categoria/categorias_detallesPapelera.html', categoria = categoria)

#--------------------------------------RESTAURAR CATEGORIA-------------------------
@categorias.route('/categorias/papelera/restaurar/<string:id>')
@login_required
def categoria_restaurar(id):
    estado = True
    fecha_modificacion = datetime.now()
    con = get_db_connection()
    cur = con.cursor()
    sql = "UPDATE categorias SET estado = %s, fecha_modificacion = %s WHERE id_categoria = %s"
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql, valores)
    con.commit()
    cur.close()
    con.close()
    flash("Categoria restaurada correctamente")
    return redirect(url_for('categorias.categorias_buscar'))