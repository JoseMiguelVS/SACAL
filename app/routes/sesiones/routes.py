from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from utils.listas import lista_cursos, lista_meses, lista_semanas

from ..utils.utils import get_db_connection, paginador2

sesiones = Blueprint('sesiones', __name__)

#-----------------------------------------BUSCAR SESION-------------------------------------
@sesiones.route("/participantes/sesiones")
@login_required
def sesiones_buscar():
    search_query = request.args.get('buscar','', type = str).strip()

    if search_query:
        sql_count = 'SELECT COUNT (*) FROM detalles_sesiones WHERE estado = true AND fecha ILIKE %s;'
        sql_lim = 'SELECT * FROM detalles_sesiones WHERE estado = true AND fecha ILIKE %s ORDER BY id_sesion DESC LIMIT %s OFFSET %s;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT (*) FROM detalles_sesiones WHERE estado = true;'
        sql_lim = 'SELECT * FROM detalles_sesiones WHERE estado = true ORDER BY id_sesion DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1, 5)

    return render_template('sesiones/sesiones.html',
                           sesiones=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)

#---------------------------------AGREGAR SESION---------------------------

@sesiones.route('/participantes/sesiones/agregar')
@login_required
def sesiones_agregar():
    titulo = 'Agregar sesion'
    return render_template('sesiones/sesiones_agregar.html', titulo = titulo, cursos = lista_cursos(), semanas = lista_semanas(), meses = lista_meses(), categorias = lista_categorias())

@sesiones.route('/participantes/sesiones/agregar/nuevo', methods=("GET", "POST"))
@login_required
def sesion_nuevo():
    if request.method == 'POST':
        nombre_curso = request.form['id_curso']
        curso1 = request.form['id_curso1']
        curso2 = request.form['id_curso2']
        curso3 = request.form['id_curso3']
        curso4 = request.form['id_curso4']
        curso5 = request.form['id_curso5']
        curso6 = request.form['id_curso6']
        curso7 = request.form['id_curso7']
        curso8 = request.form['id_curso8']
        curso9 = request.form['id_curso9']
        fecha = request.form['fecha']
        horario_inicio = request.form['horario_inicio']
        horario_fin = request.form['horario_fin']
        mes = request.form['id_mes']
        semana = request.form['id_semana']
        estado = True

        con = get_db_connection()
        cur = con.cursor(cursor_factory = RealDictCursor)
        sql = 'INSERT INTO sesiones_curso (nombre_curso,curso1, curso2, curso3, curso4, curso5, curso6, curso7, curso8, curso9, fecha, horario_inicio, horario_fin, mes, semana, estado) VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s)'
        valores = (nombre_curso, curso1, curso2, curso3, curso4, curso5, curso6, curso7, curso8, curso9, fecha, horario_inicio, horario_fin, mes, semana, estado)
        cur.execute(sql,valores)
        con.commit()
        cur.close()
        con.close()
        flash("Sesión agregada correctamente")
        return redirect(url_for('sesiones.sesiones_buscar'))

    return redirect(url_for('sesiones.sesion_agregar'))


#------------------------------------EDITAR SESION-------------------------------
@sesiones.route('/participantes/editar/<string:id>')
@login_required
def sesion_editar(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM sesiones_curso WHERE id_sesion = {0}'.format(id))
    sesiones = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('sesiones/sesiones_editar.html', sesiones = sesiones[0], cursos = lista_cursos(), semanas = lista_semanas(), meses = lista_meses())

@sesiones.route("/participantes/sesiones/editar/<string:id>", methods = ["POST"])
@login_required
def sesion_actualizar(id):
    if request.method == "POST":
        nombre_curso = request.form['id_curso']
        fecha = request.form['fecha']
        horario_inicio = request.form['horario_inicio']
        horario_fin = request.form['horario_fin']
        mes = request.form['id_mes']
        semana = request.form['id_semana']

        con = get_db_connection()
        cur = con.cursor()
        sql = "UPDATE sesiones_curso SET nombre_curso = %s, fecha = %s, horario_inicio = %s, horario_fin = %s, mes = %s, semana = %s WHERE id_sesion = %s"
        valores = (nombre_curso, fecha, horario_inicio, horario_fin, mes, semana, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash("Sesion actualizada correctamente")
    return redirect(url_for("sesiones.sesiones_buscar"))

#-----------------------------------CANCELAR SESION---------------------------------
@sesiones.route("/participantes/sesiones/cancelar/<string:id>")
@login_required
def sesion_cancelar(id):
    estado = False

    con = get_db_connection()
    cur = con.cursor()
    sql = "UPDATE sesiones_curso SET estado = %s WHERE id_sesion = %s"
    valores = (estado, id)
    cur.execute(sql, valores)
    con.commit()
    cur.close()
    con.close()
    flash("Sesion cancelada correctamente")
    return redirect(url_for('sesiones.sesiones_buscar'))

#--------------------------------------PAPELERA DE SESIONES--------------------------
@sesiones.route("/participantes/papelera/sesiones")
@login_required
def sesiones_papelera():
    search_query = request.args.get('buscar','', type = str).strip()

    if search_query:
        sql_count = 'SELECT COUNT (*) FROM detalles_sesiones WHERE estado = false AND fecha ILIKE %s;'
        sql_lim = 'SELECT * FROM detalles_sesiones WHERE estado = false AND fecha ILIKE %s ORDER BY id_sesion DESC LIMIT %s OFFSET %s;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT (*) FROM detalles_sesiones WHERE estado = false;'
        sql_lim = 'SELECT * FROM detalles_sesiones WHERE estado = false ORDER BY id_sesion DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1, 5)

    return render_template('sesiones/sesiones_papelera.html',
                           sesiones=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)

#--------------------------------RESTAURAR SESION----------------------------------
@sesiones.route("/participantes/sesiones/restaurar/<string:id>")
@login_required
def sesion_restaurar(id):
    estado = True

    con = get_db_connection()
    cur = con.cursor()
    sql = "UPDATE sesiones_curso SET estado = %s WHERE id_sesion = %s"
    valores = (estado, id)
    cur.execute(sql, valores)
    con.commit()
    cur.close()
    con.close()
    flash("Sesion restaurada correctamente")
    return redirect(url_for('sesiones.sesiones_buscar'))    