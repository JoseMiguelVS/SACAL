from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..utils.utils import get_db_connection, paginador3

participantes = Blueprint('participantes', __name__)

#-------------------------LISTA DE CUENTAS-----------------------
def lista_cuentas():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM cuentas ORDER BY id_cuenta ASC')
    cuentas = cur.fetchall()
    cur.close()
    con.close()
    return cuentas

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
    sesion = request.args.get('sesion', '', type=str)

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas
                   WHERE (%s = '' OR nombre_curso::text = %s)
                     AND (%s = '' OR fecha ILIKE %s)'''

    sql_lim = '''SELECT * FROM asistencias_detalladas
                 WHERE (%s = '' OR nombre_curso::text = %s)
                   AND (%s = '' OR fecha ILIKE %s)
                 ORDER BY nombre_participante DESC
                 LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [nombre_curso, nombre_curso, sesion, sesion],
        1, 5
    )

    return render_template('participantes/participantes.html',
                           cursos=lista_cursos(),
                           sesiones = lista_sesiones(),
                           paquetes = lista_paquetes(),
                           cuentas = lista_cuentas(),
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
        nombre_empleado = request.form['nombre_empleado']
        nombre_paquete = request.form['id_paquete']
        curso = request.form['id_curso']
        estado = True
        sesion = request.form['id_sesion']

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        # 1. Insertar participante
        sql = '''
            INSERT INTO participantes 
            (nombre_participante, num_telefono, clave_participante, nombre_paquete, nombre_empleado, estado, curso)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_participante
        '''
        valores = (nombre_participante, num_telefono, clave_participante, nombre_paquete, nombre_empleado, estado, curso)
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
    
#---------------------------------------------------------------------------------------------------------------
@participantes.route('/participantes/actualizar/<int:id>', methods=['POST'])
@login_required
def actualizar_participante(id):
    datos = request.get_json()

    con = get_db_connection()
    cur = con.cursor()

    sql = '''
        UPDATE participantes SET
            clave_participante = %s,
            nombre_participante = %s,
            nombre_paquete = %s,
            fecha_pago = %s,
            factura_pago = %s,
            cuenta_destino = %s,
            confirmacion_grupo = %s,
            materiales = %s,
            grabaciones = %s,
            evaluacion_dc3 = %s,
            observaciones = %s
        WHERE id_participante = %s
    '''
    valores = (
        datos['clave_participante'],
        datos['nombre_participante'],
        datos['nombre_paquete'],
        datos['fecha_pago'] or None,
        datos['factura_pago'],
        datos['cuenta_destino'],
        datos['confirmacion_grupo'],
        datos['materiales'],
        datos['grabaciones'],
        datos['evaluacion_dc3'],
        datos['observaciones'],
        id
    )

    cur.execute(sql, valores)
    con.commit()
    cur.close()
    con.close()

    return jsonify({'message': 'Participante actualizado correctamente'})
