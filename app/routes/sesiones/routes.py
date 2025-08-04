from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from app.utils.listas import lista_categorias, lista_cursos, lista_meses, lista_ponente, lista_semanas

from ..utils.utils import get_db_connection, paginador2

sesiones = Blueprint('sesiones', __name__)

#-----------------------------------------BUSCAR SESION-------------------------------------
@sesiones.route("/participantes/sesiones")
@login_required
def sesiones_buscar():
    search_query = request.args.get('buscar','', type = str).strip()

    if search_query:
        sql_count = 'SELECT COUNT (*) FROM detalles_sesiones WHERE estado = true AND fecha_curso ILIKE %s;'
        sql_lim = 'SELECT * FROM detalles_sesiones WHERE estado = true AND fecha_curso ILIKE %s ORDER BY id_sesion DESC LIMIT %s OFFSET %s;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT (*) FROM detalles_sesiones WHERE estado = true;'
        sql_lim = 'SELECT * FROM detalles_sesiones WHERE estado = true ORDER BY id_sesion DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1, 5)

    for sesion in paginado[0]:
        if isinstance(sesion['fecha_curso'], str):
            try:
                sesion['fecha_curso'] = datetime.strptime(sesion['fecha_curso'], "%Y-%m-%d")
            except ValueError:
                pass

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
        categoria = request.form['id_categoria']
        mes = request.form['id_mes']
        semana = request.form['id_semana']
        estado = True

        # Campos dinámicos
        cursos = request.form.getlist('cursos[]')
        ponentes = request.form.getlist('ponentes[]')
        fechas_curso = request.form.getlist('fecha_curso[]')

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        # Insertar sesión principal
        sql_sesion = '''
            INSERT INTO sesiones_curso 
            (categoria, mes, semana, estado)
            VALUES (%s, %s, %s, %s)
            RETURNING id_sesion
        '''
        valores_sesion = (categoria, mes, semana, estado)
        cur.execute(sql_sesion, valores_sesion)
        sesion_id = cur.fetchone()['id_sesion']

        # Insertar cursos y ponentes
        sql_relacion = '''
            INSERT INTO cursos_sesion (sesion_id, curso_id, ponente_id, fecha_curso)
            VALUES (%s, %s, %s, %s)
        '''
        for curso_id, ponente_id, fechas_curso in zip(cursos, ponentes, fechas_curso):
            cur.execute(sql_relacion, (sesion_id, curso_id, ponente_id, fechas_curso))

        con.commit()
        cur.close()
        con.close()

        flash("Sesión y cursos registrados correctamente.")
        return redirect(url_for('sesiones.sesiones_buscar'))

    return redirect(url_for('sesiones.sesiones_agregar'))

#------------------------------------EDITAR SESION-------------------------------
from datetime import datetime

@sesiones.route('/participantes/sesiones/editar/<string:id>')
@login_required 
def sesion_editar(id):
    con = get_db_connection()
    cur = con.cursor()

    # Obtener datos generales de la sesión
    cur.execute("SELECT * FROM sesiones_curso WHERE id_sesion = %s;", (id,))
    sesion = cur.fetchone()

    # Obtener cursos y ponentes de la sesión
    cur.execute(
        """
        SELECT ce.curso_id,
               c.nombre_curso,
               ce.ponente_id,
               p.nombre_ponente,
               ce.fecha_curso
        FROM cursos_sesion ce
        JOIN cursos c ON c.id_curso = ce.curso_id
        JOIN ponentes p ON p.id_ponentes = ce.ponente_id
        WHERE ce.sesion_id = %s;
        """, (id,))
    
    cursos_ponentes = []
    for row in cur.fetchall():
        fecha_curso = row[4]
        # ✅ Convertir a string ISO si no es None
        # fecha_curso = fecha_curso.strftime('%Y-%m-%d') if isinstance(fecha_curso, datetime) else ''
        
        cursos_ponentes.append({
            'curso_id': row[0],
            'curso_nombre': row[1],
            'ponente_id': row[2],
            'ponente_nombre': row[3],
            'fecha_curso': fecha_curso
        })

    # Listas para selects
    cur.execute("SELECT id_curso, nombre_curso FROM cursos;")
    todos_los_cursos = cur.fetchall()

    cur.execute("SELECT id_ponentes, nombre_ponente FROM ponentes;")
    todos_los_ponentes = cur.fetchall()

    cur.execute("SELECT id_categoria, nombre_categoria FROM categorias;")
    categorias = cur.fetchall()

    cur.execute("SELECT id_mes, nombre_mes FROM meses;")
    meses = cur.fetchall()

    cur.execute("SELECT id_semana, semana FROM semanas;")
    semanas = cur.fetchall()

    cur.close()
    con.close()

    return render_template('sesiones/sesiones_editar.html',
        sesiones=sesion,
        cursos_sesion=cursos_ponentes,
        cursos=todos_los_cursos,
        ponentes=todos_los_ponentes,
        categorias=categorias,
        semanas=semanas,
        meses=meses
    )

@sesiones.route("/participantes/sesiones/editar/<string:id>", methods=["POST"])
@login_required
def sesion_actualizar(id):
    # Campos generales
    categoria = request.form['id_categoria']
    mes = request.form['id_mes']
    semana = request.form['id_semana']

    # Listas de cursos y ponentes
    cursos = request.form.getlist('cursos[]')
    ponentes = request.form.getlist('ponentes[]')
    fecha_curso = request.form.getlist('fecha_curso[]')

    if len(cursos) != len(ponentes) != len(fecha_curso):
        flash("Error: La cantidad de cursos y ponentes no coincide", "Error")
        return redirect(url_for("sesiones.sesiones_buscar"))

    con = get_db_connection()
    cur = con.cursor()

    try:
        # Actualiza sesión
        cur.execute("""
            UPDATE sesiones_curso 
            SET categoria = %s, mes = %s, semana = %s 
            WHERE id_sesion = %s
        """, (categoria, mes, semana, id))

        # Elimina los registros anteriores de cursos/ponentes
        cur.execute("DELETE FROM cursos_sesion WHERE sesion_id = %s", (id,))

        # Inserta nuevas combinaciones
        insert_sql = """
            INSERT INTO cursos_sesion (sesion_id, curso_id, ponente_id, fecha_curso)
            VALUES (%s, %s, %s; %s)
        """
        for curso, ponente, fecha_curso in zip(cursos, ponentes, fecha_curso):
            cur.execute(insert_sql, (id, curso, ponente, fecha_curso))

        con.commit()
        flash("Sesión actualizada correctamente", "success")

    except Exception as e:
        con.rollback()
        flash(f"Error al actualizar la sesión: {e}", "Error")

    finally:
        cur.close()
        con.close()

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

    for sesion in paginado[0]:
        if isinstance(sesion['fecha'], str):
            try:
                sesion['fecha'] = datetime.strptime(sesion['fecha'], "%Y-%m-%d")
            except ValueError:
                pass

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