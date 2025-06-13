from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from utils.listas import lista_categorias, lista_cursos, lista_meses, lista_ponente, lista_semanas

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
                           cursos = lista_cursos(), 
                           semanas = lista_semanas(), 
                           meses = lista_meses(), 
                           categorias = lista_categorias(),
                           ponentes = lista_ponente(),
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
    return render_template('sesiones/sesiones_agregar.html', titulo = titulo, 
                           cursos = lista_cursos(), 
                           semanas = lista_semanas(), 
                           meses = lista_meses(), 
                           categorias = lista_categorias(),
                           ponentes = lista_ponente())

@sesiones.route('/participantes/sesiones/agregar/nuevo', methods=("GET", "POST"))
@login_required
def sesion_nuevo():
    if request.method == 'POST':
        # Campos base
        fecha = request.form['fecha']
        horario_inicio = request.form['horario_inicio']
        horario_fin = request.form['horario_fin']
        categoria = request.form['id_categoria']
        mes = request.form['id_mes']
        semana = request.form['id_semana']
        estado = True

        # Campos dinámicos
        cursos = request.form.getlist('cursos[]')
        ponentes = request.form.getlist('ponentes[]')

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        # Insertar sesión principal
        sql_sesion = '''
            INSERT INTO sesiones_curso 
            (fecha, horario_inicio, horario_fin, categoria, mes, semana, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_sesion
        '''
        valores_sesion = (fecha, horario_inicio, horario_fin, categoria, mes, semana, estado)
        cur.execute(sql_sesion, valores_sesion)
        sesion_id = cur.fetchone()['id_sesion']

        # Insertar cursos y ponentes
        sql_relacion = '''
            INSERT INTO cursos_sesion (sesion_id, curso_id, ponente_id)
            VALUES (%s, %s, %s)
        '''
        for curso_id, ponente_id in zip(cursos, ponentes):
            cur.execute(sql_relacion, (sesion_id, curso_id, ponente_id))

        con.commit()
        cur.close()
        con.close()

        flash("Sesión y cursos registrados correctamente.")
        return redirect(url_for('sesiones.sesiones_buscar'))

    return redirect(url_for('sesiones.sesiones_agregar'))


#------------------------------------EDITAR SESION-------------------------------
@sesiones.route('/participantes/sesiones/editar/<string:id>')
@login_required
def sesion_editar(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM sesiones_curso WHERE id_sesion = {0}'.format(id))
    sesiones = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('sesiones/sesiones_editar.html', 
                           sesiones = sesiones[0], 
                           cursos = lista_cursos(), 
                           semanas = lista_semanas(), 
                           meses = lista_meses(),
                           categorias = lista_categorias(),
                           ponentes = lista_ponente())

@sesiones.route("/participantes/sesiones/editar/<string:id>", methods=["POST"])
@login_required
def sesion_actualizar(id):
    if request.method == "POST":
        # Campos generales
        fecha = request.form['fecha']
        horario_inicio = request.form['horario_inicio']
        horario_fin = request.form['horario_fin']
        categoria = request.form['id_categoria']
        mes = request.form['id_mes']
        semana = request.form['id_semana']

        # Listas de cursos y ponentes
        cursos = request.form.getlist('cursos[]')
        ponentes = request.form.getlist('ponentes[]')

        con = get_db_connection()
        cur = con.cursor()

        # Actualiza sesión
        sql_update_sesion = """
            UPDATE sesiones_curso 
            SET fecha = %s, horario_inicio = %s, horario_fin = %s, categoria = %s, mes = %s, semana = %s 
            WHERE id_sesion = %s
        """
        cur.execute(sql_update_sesion, (fecha, horario_inicio, horario_fin, categoria, mes, semana, id))

        # Elimina cursos/ponentes anteriores
        cur.execute("DELETE FROM cursos_sesion WHERE sesion_id = %s", (id,))

        # Inserta nuevas combinaciones
        sql_insert_cs = """
            INSERT INTO cursos_sesion (sesion_id, curso_id, ponente_id)
            VALUES (%s, %s, %s)
        """
        for curso, ponente in zip(cursos, ponentes):
            cur.execute(sql_insert_cs, (id, curso, ponente))

        con.commit()
        cur.close()
        con.close()

        flash("Sesión actualizada correctamente")

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
@sesiones.route("/participantes/sesiones/papelera")
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