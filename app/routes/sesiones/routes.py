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
        
        sql_gastos = '''
            INSERT INTO gastos_sesiones
            (sesion_id, publicidad, honorarios  )
            VALUES (%s, %s, %s)
            '''
            
        valores_gastos = (sesion_id, 0, 0)
        cur.execute(sql_gastos, valores_gastos)

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
        SELECT ce.id_cursoesp,
            ce.curso_id,
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
        fecha_curso = row[5]  # índice 5 es fecha_curso

        # Si quieres formatear fecha:
        # if fecha_curso:
        #     fecha_curso = fecha_curso.strftime('%Y-%m-%d')

        cursos_ponentes.append({
            'id_cursoesp': row[0],      # ID de la fila para update
            'curso_id': row[1],
            'curso_nombre': row[2],
            'ponente_id': row[3],
            'ponente_nombre': row[4],
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
    categoria = request.form['id_categoria']
    mes = request.form['id_mes']
    semana = request.form['id_semana']

    # Listas de datos enviados desde el formulario
    ids = request.form.getlist('id_cursos_sesion[]')  # String IDs (algunos vacíos)
    cursos = request.form.getlist('cursos[]')
    ponentes = request.form.getlist('ponentes[]')
    fechas = request.form.getlist('fecha_curso[]')

    # Validar longitudes
    if not (len(ids) == len(cursos) == len(ponentes) == len(fechas)):
        flash("Error: La cantidad de datos enviados no coincide", "Error")
        return redirect(url_for("sesiones.sesiones_buscar"))

    con = get_db_connection()
    cur = con.cursor()

    try:
        # 1. Obtener IDs originales de cursos de la sesión
        cur.execute("SELECT id_cursoesp FROM cursos_sesion WHERE sesion_id = %s", (id,))
        ids_originales = set(str(row[0]) for row in cur.fetchall())  # Convertir a str para comparar

        # 2. Filtrar IDs válidos que el usuario mantuvo
        ids_actualizados = set(i.strip() for i in ids if i.strip().isdigit())

        # 3. Determinar IDs eliminados (presentes antes, pero no enviados ahora)
        ids_eliminados = ids_originales - ids_actualizados

        # 4. Eliminar de la base de datos
        for id_eliminar in ids_eliminados:
            cur.execute("DELETE FROM cursos_sesion WHERE id_cursoesp = %s", (id_eliminar,))

        # 5. Actualizar sesión general
        cur.execute("""
            UPDATE sesiones_curso 
            SET categoria = %s, mes = %s, semana = %s 
            WHERE id_sesion = %s
        """, (categoria, mes, semana, id))

        # 6. Insertar o actualizar cursos
        for id_curso_sesion, curso, ponente, fecha in zip(ids, cursos, ponentes, fechas):
            if id_curso_sesion and id_curso_sesion.strip().isdigit():
                # Actualizar
                cur.execute("""
                    UPDATE cursos_sesion
                    SET curso_id = %s, ponente_id = %s, fecha_curso = %s
                    WHERE id_cursoesp = %s
                """, (curso, ponente, fecha, id_curso_sesion))
            else:
                # Insertar nuevo
                cur.execute("""
                    INSERT INTO cursos_sesion (sesion_id, curso_id, ponente_id, fecha_curso)
                    VALUES (%s, %s, %s, %s)
                """, (id, curso, ponente, fecha))

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