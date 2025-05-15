from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..utils.utils import get_db_connection, paginador3

participantes = Blueprint('participantes', __name__)

#--------------------------LISTA DE SESIONES---------------------
def lista_sesiones():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM detalles_sesiones ORDER BY id_sesion ASC')
    sesiones = cur.fetchall()
    cur.close()
    con.close()
    return sesiones

 #---------------------------------------LISTA DE CURSOS--------------------------------

#---------------------------------------LISTA DE CURSOS-----------------------
def lista_cursos():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM cursos ORDER BY id_curso ASC')
    cursos = cur.fetchall()
    cur.close()
    con.close()
    return cursos

#---------------------------------LISTA SEMANAS-------------------------------
def lista_semanas():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM semanas ORDER BY id_semana ASC')
    semanas = cur.fetchall()
    cur.close()
    con.close()
    return semanas

#------------------------------LISTA DE MESES-------------------
def lista_meses():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM meses ORDER BY id_mes ASC')
    meses = cur.fetchall()
    cur.close()
    con.close()
    return meses

#------------------------------LISTA DE PAQUETES----------------------------------
def lista_paquetes():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM paquetes ORDER BY id_paquete ASC')
    paquetes = cur.fetchall()
    cur.close()
    con.close()
    return paquetes
#---------------------------------------------------------------PARTICIPANTES-----------------------------------------------------------------------------------------------------
@participantes.route("/participantes")
@login_required
def participantes_buscar():
    nombre_curso = request.args.get('nombre_curso', '', type=str)
    nombre_mes = request.args.get('nombre_mes', '', type=str)
    nombre_semana = request.args.get('semana', '', type=str)

    sql_count = '''SELECT COUNT(*) FROM vista_asistencias_detalladas
                   WHERE (%s = '' OR nombre_curso::text = %s)
                     AND (%s = '' OR nombre_mes::text = %s)
                     AND (%s = '' OR semana::text = %s)'''

    sql_lim = '''SELECT * FROM vista_asistencias_detalladas
                 WHERE (%s = '' OR nombre_curso::text = %s)
                   AND (%s = '' OR nombre_mes::text = %s)
                   AND (%s = '' OR semana::text = %s)
                 ORDER BY nombre_participante DESC
                 LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [nombre_curso, nombre_curso, nombre_mes, nombre_mes, nombre_semana, nombre_semana],
        1, 5
    )

    return render_template('participantes/participantes.html',
                           cursos=lista_cursos(),
                           semanas=lista_semanas(),
                           meses=lista_meses(),
                           participantes=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4])

@participantes.route("/participantes/agregar")
@login_required
def participante_agregar():
    titulo = 'Agregar participante'
    return render_template('participantes/participantes_agregar.html', 
                           cursos = lista_cursos(),
                           sesiones = lista_sesiones(),
                           paquetes = lista_paquetes())

@participantes.route('/participantes/agregar/nuevo', methods=('GET', 'POST'))
@login_required
def participante_nuevo():
    if request.method == 'POST':
        nombre_participante = request.form['nombre_participante']
        num_telefono = request.form['num_telefono']
        clave_participante = request.form['clave_participante']
        nombre_paquete = request.form['id_paquete']
        curso = request.form['id_curso']
        estado = True
        sesion = request.form['id_sesion']

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        # 1. Insertar participante
        sql = '''
            INSERT INTO participantes 
            (nombre_participante, num_telefono, clave_participante, nombre_paquete, estado, curso)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_participante
        '''
        valores = (nombre_participante, num_telefono, clave_participante, nombre_paquete, estado, curso)
        cur.execute(sql, valores)

        # 2. Obtener el ID recién creado
        participante_id = cur.fetchone()['id_participante']

        # 3. Insertar asistencia
        sql2 = 'INSERT INTO asistencias (participante, sesion) VALUES (%s, %s)'
        valores2 = (participante_id, sesion)
        cur.execute(sql2, valores2)

        # 4. Guardar cambios y cerrar conexión
        con.commit()
        cur.close()
        con.close()

        flash('Participante y asistencia registrados correctamente.')
        return redirect(url_for('participantes.participantes_buscar'))  # o redirige a donde quieras
