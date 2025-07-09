from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from utils.listas import lista_temas

from ..utils.utils import get_db_connection, paginador1

# Definir Blueprint 
cursos = Blueprint('cursos', __name__)

#-------------------------------BUSCAR CURSO--------------------------
@cursos.route("/cursos")
@login_required
def cursos_buscar():
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM detalles_curso WHERE estado = true AND (nombre_curso ILIKE %s OR codigo_curso ILIKE %s);'
    sql_lim = 'SELECT * FROM detalles_curso WHERE estado = true AND (nombre_curso ILIKE %s OR codigo_curso ILIKE %s) ORDER BY id_curso DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count,sql_lim, search_query, 1, 5)
    return render_template('cursos/cursos.html',
                           temas = lista_temas(),
                           cursos=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query = search_query)

#--------------------------------------AGREGAR CURSO-----------------------
@cursos.route("/cursos/agregar")
@login_required
def curso_agregar():
    titulo = 'Agregar curso'
    return render_template('cursos/cursos_agregar.html', titulo = titulo, temas = lista_temas())

@cursos.route("/cursos/agregar/nuevo", methods=('GET', 'POST'))
@login_required
def cursos_nuevo():
    if request.method == 'POST':
        codigo_curso = request.form['codigo_curso']
        nombre_curso = request.form['nombre_curso']
        tema_curso = request.form['id_tema']
        duracion_curso = request.form['duracion_curso']

        # Validación para 'es_nacional': si no viene, asignar None
        es_nacional = request.form.get('es_nacional') or None

        estado = True
        fecha_creacion = datetime.now()
        fecha_modificacion = datetime.now()

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)
        sql_validar = 'SELECT COUNT(*) FROM cursos WHERE nombre_curso = %s'
        cur.execute(sql_validar, (nombre_curso,))
        existe = cur.fetchone()['count']
        if existe:
            cur.close()
            con.close()
            flash('Error: el curso ya existe. Intente con otro')
            return redirect(url_for('cursos.curso_agregar'))
        else:
            sql = '''INSERT INTO cursos 
                     (nombre_curso, codigo_curso, tema_curso, duracion_curso, es_nacional, estado, fecha_creacion, fecha_modificacion) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
            valores = (nombre_curso, codigo_curso, tema_curso, duracion_curso, es_nacional, estado, fecha_creacion, fecha_modificacion)
            cur.execute(sql, valores)
            con.commit()
            cur.close()
            con.close()
            flash('Curso agregado correctamente')
            return redirect(url_for('cursos.cursos_buscar'))
    return redirect(url_for('cursos.curso_agregar'))

#----------------------------------DETALLES DE CURSOS---------------------------
@cursos.route('/cursos/detalles/<int:id>')
@login_required
def curso_detalles(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM detalles_curso WHERE id_curso = %s',(id,))
            curso = cur.fetchone()
    if curso is None:
        flash('El curso no existe o ha sido eliminado.')
        return redirect(url_for('cursos.cursos_buscar'))
    return render_template('cursos/curso_detalles.html', curso = curso)

#---------------------------------EDITAR CURSO-----------------------------------
@cursos.route('/cursos/editar/<string:id>')
@login_required
def curso_editar(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM cursos WHERE id_curso={0}'.format(id))
    curso = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('cursos/curso_editar.html',curso = curso[0], temas = lista_temas() )

@cursos.route('/cursos/editar/<string:id>', methods=['POST', 'GET'])
@login_required
def curso_actualizar(id):
    if request.method == 'POST':
        nombre_curso = request.form['nombre_curso']
        codigo_curso = request.form['codigo_curso']
        tema_curso = request.form['id_tema']
        duracion_curso = request.form['duracion_curso']
        es_nacional = request.form.get('es_nacional') or None
        fecha_modificacion= datetime.now()
        
        con = get_db_connection()
        cur = con.cursor()
        sql="UPDATE cursos SET nombre_curso = %s, codigo_curso = %s, tema_curso = %s, duracion_curso = %s, es_nacional = %s, fecha_modificacion = %s WHERE id_curso = %s"
        valores=(nombre_curso, codigo_curso, tema_curso, duracion_curso, es_nacional, fecha_modificacion, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash("Curso actualizado correctamente")
    return redirect(url_for('cursos.cursos_buscar'))

#---------------------------ELIMINAR CURSO------------------------------
@cursos.route('/cursos/eliminar/<string:id>')
@login_required
def curso_eliminar(id):
    estado = False
    fecha_modificacion= datetime.now()
        
    con = get_db_connection()
    cur = con.cursor()
    sql="UPDATE cursos SET estado= %s, fecha_modificacion=%s WHERE id_curso=%s"
    valores=(estado,fecha_modificacion,id)
    cur.execute(sql,valores)
    con.commit()
    cur.close()
    con.close()
    flash("Curso eliminado correctamente")
    return redirect(url_for('cursos.cursos_buscar'))

#--------------------------------PAPELERA DE CURSOS---------------------------------
@cursos.route("/cursos/papelera")
@login_required
def cursos_papelera():
    search_query = request.args.get('buscar', '', type=str)
    sql_count = 'SELECT COUNT(*) FROM detalles_curso WHERE estado = False AND (nombre_curso ILIKE %s OR codigo_curso ILIKE %s);'
    sql_lim = 'SELECT * FROM detalles_curso WHERE estado = False AND (nombre_curso ILIKE %s OR codigo_curso ILIKE %s) ORDER BY id_curso DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count,sql_lim, search_query, 1, 5)
    return render_template('cursos/cursos_papelera.html',
                           cursos=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query = search_query)

#-----------------------------------------DETALLES DE CURSO ELIMINADO----------------------
@cursos.route('/cursos/papelera/detalles/<int:id>')
@login_required
def curso_detallesPapelera(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM detalles_curso WHERE id_curso = %s',(id,))
            curso = cur.fetchone()
    if curso is None:
        flash('El curso no existe o ha sido eliminado.')
        return redirect(url_for('cursos.cursos_buscar'))
    return render_template('cursos/curso_detallesPepelera.html', curso = curso)

#--------------------------------------RESTAURAR CURSO--------------------------------
@cursos.route('/cursos/papelera/restaurar/<string:id>')
@login_required
def curso_restaurar(id):
    estado = True
    fecha_modificacion= datetime.now()
        
    con = get_db_connection()
    cur = con.cursor()
    sql="UPDATE cursos SET estado= %s, fecha_modificacion=%s WHERE id_curso=%s"
    valores=(estado,fecha_modificacion,id)
    cur.execute(sql,valores)
    con.commit()
    cur.close()
    con.close()
    flash("Curso restaurado correctamente")
    return redirect(url_for('cursos.cursos_buscar'))