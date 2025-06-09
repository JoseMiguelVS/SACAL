from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from utils.listas import lista_cuentas, lista_cursos, lista_meses, lista_paquetes, lista_sesiones, lista_semanas

from ..utils.utils import get_db_connection, paginador3

participantes = Blueprint('participantes', __name__) 

#---------------------------------------------------------------PARTICIPANTES--------------------------------------------------------------------------
@participantes.route("/participantes")
@login_required
def participantes_buscar():
    nombre_curso = request.args.get('nombre_curso', '', type=str)
    sesion = request.args.get('sesion', '', type=str)

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas
                   WHERE (%s = '' OR cursos::text = %s)
                     AND (%s = '' OR fecha ILIKE %s)'''

    sql_lim = '''SELECT * FROM asistencias_detalladas
                 WHERE (%s = '' OR cursos::text = %s)
                   AND (%s = '' OR fecha ILIKE %s)
                 ORDER BY nombre_participante DESC
                 LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [nombre_curso, nombre_curso, sesion, sesion],
        1, 50
    )

    return render_template('participantes/participantes.html',
                           mes = lista_meses(),
                           cursos = lista_cursos(),
                           semanas = lista_semanas(),
                           sesiones = lista_sesiones(),
                           paquetes = lista_paquetes(),
                           cuentas = lista_cuentas(),
                           participantes=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4])
#-----------------------------------------------------------------------------------------

@participantes.route("/participantes/agregar")
@login_required
def participante_agregar():
    return render_template('participantes/participantes_agregar.html', 
                           cursos = lista_cursos(),
                           sesiones = lista_sesiones(),
                           cuentas = lista_cuentas(),
                           paquetes = lista_paquetes())

@participantes.route('/participantes/agregar/nuevo', methods=('GET', 'POST'))
@login_required
def participante_nuevo():
    if request.method == 'POST':
        nombre_participante = request.form['nombre_participante']
        apellidos_participante = request.form['apellidos_participante']
        num_telefono = request.form['num_telefono']
        clave_participante = request.form['clave_participante']
        nombre_empleado = request.form['nombre_empleado']
        cuenta_destino = request.form['id_cuenta']
        nombre_paquete = request.form['id_paquete']
        sesion = request.form['id_sesion']
        estado = True
        constancia_generada = False
        constancia_enviada = False

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        # 1. Insertar participante
        sql = '''
            INSERT INTO participantes 
            (nombre_participante,apellidos_participante, num_telefono, clave_participante, nombre_paquete, nombre_empleado, estado, cuenta_destino)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_participante
        '''
        valores = (nombre_participante,apellidos_participante, num_telefono, clave_participante, nombre_paquete, nombre_empleado, estado, cuenta_destino )
        cur.execute(sql, valores)

        # 2. Obtener el ID recién creado
        participante_id = cur.fetchone()['id_participante']

        # 3. Insertar asistencia
        sql2 = 'INSERT INTO asistencias (participante, sesion) VALUES (%s, %s) RETURNING id'
        valores2 = (participante_id, sesion)
        cur.execute(sql2, valores2)

        # 3.5 Obtener el id de asistencia
        asistencia_id = cur.fetchone()['id']

        sql3 = "INSERT INTO constancias (participante, constancia_generada, constancia_enviada, asistencia) VALUES (%s, %s, %s, %s)"
        valores3 = (participante_id, constancia_generada, constancia_enviada, asistencia_id)
        cur.execute(sql3, valores3)

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
            apellidos_participante = %s,
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
        datos['apellidos_participante'],
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