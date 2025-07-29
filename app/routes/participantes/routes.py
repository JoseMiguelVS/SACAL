import os
import re
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

from app.utils.listas import lista_cuentas, lista_cursos, lista_equipos, lista_formaPago, lista_meses, lista_paquetes, lista_sesiones, lista_semanas

from ..utils.utils import allowed_file, get_db_connection, my_random_string, paginador3

from supabase import create_client
import io

SUPABASE_URL = "https://ipecmsarkhzdzkkanxvj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlwZWNtc2Fya2h6ZHpra2FueHZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3MjY4ODAsImV4cCI6MjA2OTMwMjg4MH0.dy4dSDzoTifaRTU-wQnl6oju1iiYdxHN-p0kBbYU1lI"
BUCKET_NAME = "tickets"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

participantes = Blueprint('participantes', __name__) 

#---------------------------------------------------------------PARTICIPANTES--------------------------------------------------------------------------
@participantes.route("/participantes")
@login_required
def participantes_buscar():
    search_query = request.args.get('buscar', '', type=str).strip()
    search_query_sql = f"%{search_query}%"

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas
                   WHERE (nombre_participante ILIKE %s OR clave_participante ILIKE %s)
                   AND grabacion = False
                   '''

    sql_lim = '''SELECT * FROM asistencias_detalladas
                 WHERE (nombre_participante ILIKE %s OR clave_participante ILIKE %s)
                 AND grabacion = False
                 ORDER BY nombre_participante DESC
                 LIMIT %s OFFSET %s'''

    paginado = paginador3(sql_count, sql_lim, [search_query_sql, search_query_sql], 1, 50)

    return render_template('participantes/participantes.html',
                           formas = lista_formaPago(),
                           equipos=lista_equipos(),
                           cursos=lista_cursos(),
                           sesiones=lista_sesiones(),
                           paquetes=lista_paquetes(),
                           cuentas=lista_cuentas(),
                           meses=lista_meses(),
                           semanas=lista_semanas(),
                           participantes=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)

@participantes.route("/participantes/filtros")
@login_required
def participantes_filtros():
    equipos = request.args.get('equipos', '', type=str)
    mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)
    fecha_raw = request.args.get('fecha', '', type=str)

    fecha = ''
    cursos = ''
    equipo = ''
    if fecha_raw:
        partes = fecha_raw.split('/')
        if len(partes) == 3:
            fecha = partes[1]
            cursos = partes[2]

    if equipos:
        partesEquipos = equipos.split(',')
        if len(partesEquipos) == 2:
            equipo = partesEquipos[1]

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas
                WHERE (%s = '' OR meses ILIKE %s)
                    AND (%s = '' OR nombre_equipo ILIKE %s)
                    AND (%s = '' OR semanas ILIKE %s)
                    AND (%s = '' OR fecha ILIKE %s)
                    AND (%s = '' OR cursos ILIKE %s)
                    AND grabacion    = False ''' 

    sql_lim = '''SELECT * FROM asistencias_detalladas
                WHERE (%s = '' OR meses ILIKE %s)
                    AND (%s = '' OR nombre_equipo ILIKE %s)
                    AND (%s = '' OR semanas ILIKE %s)
                    AND (%s = '' OR fecha ILIKE %s)
                    AND (%s = '' OR cursos ILIKE %s)
                    AND grabacion    = False
                ORDER BY nombre_participante DESC
                LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [
            mes, mes,
            equipo, equipo,
            semana, semana,
            fecha, fecha,
            cursos, cursos,
        ],
        1, 50   
    )

    return render_template('participantes/participantes.html',
                           formas =lista_formaPago(),
                           equipos=lista_equipos(),
                           meses=lista_meses(),
                           cursos=lista_cursos(),
                           semanas=lista_semanas(),
                           sesiones=lista_sesiones(),
                           paquetes=lista_paquetes(),
                           cuentas=lista_cuentas(),
                           participantes=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4])

@participantes.route("/participantes/grabaciones")
@login_required
def participantes_grabaciones():
    search_query = request.args.get('buscar', '', type=str)
    equipos = request.args.get('equipos', '', type=str)
    mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)
    fecha_raw = request.args.get('fecha', '', type=str)

    fecha = ''
    cursos = ''
    equipo = ''
    if fecha_raw:
        partes = fecha_raw.split('/')
        if len(partes) == 3:
            fecha = partes[1]
            cursos = partes[2]
    if equipos:
        partesEquipos = equipos.split(',')
        if len(partesEquipos) == 2:
            equipo = partesEquipos[1]

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas
                WHERE (%s = '' OR meses ILIKE %s)
                    AND (%s = '' OR nombre_equipo ILIKE %s)
                    AND (%s = '' OR semanas ILIKE %s)
                    AND (%s = '' OR fecha ILIKE %s)
                    AND (%s = '' OR cursos ILIKE %s)
                    AND (%s = '' OR nombre_participante ILIKE %s OR clave_participante ILIKE %s)
                    AND grabaciones = 'True' ''' 

    sql_lim = '''SELECT * FROM asistencias_detalladas
                WHERE (%s = '' OR meses ILIKE %s)
                    AND (%s = '' OR nombre_equipo ILIKE %s)
                    AND (%s = '' OR semanas ILIKE %s)
                    AND (%s = '' OR fecha ILIKE %s)
                    AND (%s = '' OR cursos ILIKE %s)
                    AND (%s = '' OR nombre_participante ILIKE %s OR clave_participante ILIKE %s)
                    AND grabaciones = 'True'
                ORDER BY nombre_participante DESC
                LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [
            mes, mes,
            equipo, equipo,
            semana, semana,
            fecha, fecha,
            cursos, cursos,
            search_query, search_query, search_query  # nombre y clave usan el mismo valor
        ],
        1, 50
    )

    return render_template('participantes/participantes_grabaciones.html',
                           formas =lista_formaPago(),
                           equipos=lista_equipos(),
                           meses=lista_meses(),
                           cursos=lista_cursos(),
                           semanas=lista_semanas(),
                           sesiones=lista_sesiones(),
                           paquetes=lista_paquetes(),
                           cuentas=lista_cuentas(),
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
                           formas = lista_formaPago(),
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
        num_telefono = re.sub(r'\D', '', request.form['num_telefono'])
        clave_participante = request.form['clave_participante']
        nombre_empleado = request.form['nombre_empleado']
        paquete = request.form['paquete']
        sesion = request.form['id_sesion']
        equipos = request.form['equipos']
        estado = True
        constancia_generada = False
        constancia_enviada = False

        nombre_paquete = ''
        precio_paquete = ''
        if paquete:
            partes = paquete.split(',')
            if len(partes) == 2:
                nombre_paquete = partes[0].strip()
                precio_paquete = partes[1].strip()

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        # 1. Insertar participante
        sql = '''
            INSERT INTO participantes 
            (nombre_participante,apellidos_participante, num_telefono, clave_participante, nombre_paquete, nombre_empleado, estado, equipos)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_participante
        '''
        valores = (nombre_participante,apellidos_participante, num_telefono, clave_participante, nombre_paquete, nombre_empleado, estado, equipos )
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

        sql4 = "INSERT INTO pagos (ingresos, participante, validacion_pago, concepto_factura) VALUES (%s, %s, %s, %s)"
        valores4 = (precio_paquete, participante_id,'1','3')
        cur.execute(sql4, valores4)

        # 4. Guardar cambios y cerrar conexión
        con.commit()
        cur.close()
        con.close()

        flash('Participante y asistencia registrados correctamente.')
        return redirect(url_for('participantes.participantes_buscar'))
    
#---------------------------------------------------------------------------------------------------------------
@participantes.route('/participantes/actualizar/<int:id>', methods=['POST'])
@login_required
def actualizar_participante(id):
    datos = request.get_json()

    con = get_db_connection()
    cur = con.cursor()

    # ------------------- Actualiza los datos del participante -------------------
    sql_participante = '''
        UPDATE participantes SET
            clave_participante = %s,
            num_telefono = %s,
            nombre_participante = %s,
            apellidos_participante = %s,
            nombre_paquete = %s,
            fecha_pago = %s,
            factura_pago = %s,
            forma_pago = %s,
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
        datos['num_telefono'],
        datos['apellidos_participante'],
        datos['nombre_paquete'],
        datos['fecha_pago'] or None,
        datos['factura_pago'],
        datos['id_forma'],
        datos['cuenta_destino'],
        datos['confirmacion_grupo'],
        datos['materiales'],
        datos['grabaciones'],
        datos['evaluacion_dc3'],
        datos['observaciones'],
        id
    )
    cur.execute(sql_participante, valores)

    # ------------------- Calcula ingreso_factura con IVA 16% -------------------
    try:
        ingresos = float(datos['ingresos'])
        ingreso_factura = round(ingresos * 1.16, 2)
    except (KeyError, ValueError):
        ingreso_factura = None  # o puedes manejar un valor por defecto

    # ------------------- Actualiza tabla pagos -------------------
    sql_pago = '''
        UPDATE pagos 
        SET ingreso_factura = %s, fecha_pago = %s, ingresos = '0'
        WHERE participante = %s
    '''
    cur.execute(sql_pago, (
        ingreso_factura,
        datos['fecha_pago'] or None,
        id
    ))

    # ------------------- Finaliza conexión -------------------
    con.commit()
    cur.close()
    con.close()

    return jsonify({'alert': 'Participante actualizado correctamente'})

@participantes.route('/participantes/actualizar/sesion/<string:id>', methods=['POST'])
@login_required
def participante_actualizar(id):
    if request.method == 'POST':
        sesion = request.form['sesion']
        grabacion = request.form['grabacion']

        grabacion_new = ''
        if grabacion == 'on':
            grabacion_new = 'True'

        con = get_db_connection()
        cur = con.cursor()
        sql = "UPDATE asistencias SET sesion = %s WHERE participante = %s"
        valores = (sesion, id)
        cur.execute(sql,valores)

        sql2 = "UPDATE participantes SET grabacion = %s WHERE id_participante = %s"
        valores2 = (grabacion_new, id)
        cur.execute(sql2,valores2)
        con.commit()
        cur.close()
        con.close()
        flash("Participante cambiado de sesion")
    return redirect(url_for('participantes.participantes_buscar'))

@participantes.route('/participantes/comprobante/<string:id>', methods=['POST'])
@login_required
def participante_comprobante(id):
    nombre_participante = request.form['nombre_participante'].strip()
    apellidos_participante = request.form['apellidos_participante'].strip()
    clave_participante = request.form['clave_participante'].strip()
    cuenta_destino = request.form['id_cuenta']
    forma_pago = request.form['id_forma']
    creado = datetime.now()

    imagenes = request.files.getlist('fotos')
    ruta = current_app.config['UPLOAD_FOLDER']

    con = get_db_connection()
    cur = con.cursor()

    sql1 = '''
                UPDATE pagos SET cuenta_destino = %s, forma_pago = %s WHERE id_participantes = %s
           '''
    valores1 = (cuenta_destino, forma_pago, id)

    cur.execute(sql1, valores1)

    for imagen in imagenes:
        if imagen and allowed_file(imagen.filename):
            cadena_aleatoria = my_random_string()
            nombre_archivo = f"{nombre_participante}_{apellidos_participante}_{clave_participante}_{creado.strftime('%Y-%m-%d')}_{cadena_aleatoria}_{secure_filename(imagen.filename)}"
            file_path = os.path.join(ruta, nombre_archivo)

            # Leer imagen como binario
            imagen_bytes = imagen.read()
            path_remoto = f"{clave_participante}/{nombre_archivo}"

            # Subir a Supabase Storage
            supabase.storage.from_(BUCKET_NAME).upload(path_remoto, imagen_bytes, file_options={"content-type": imagen.content_type}, upsert=True)


        cur.execute(
                    '''
                    INSERT INTO comprobantes_pago (participante_id, comprobante_img, fecha_creacion)
                    VALUES (%s, %s, %s)
                    ''',
                        (id, path_remoto, creado)
                    )


    con.commit()
    cur.close()
    con.close()

    flash('Comprobantes subidos correctamente')
    return redirect(url_for('participantes.participantes_buscar'))
