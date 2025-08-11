import os
import re
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from datetime import datetime, date
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

from app.utils.listas import lista_cuentas, lista_cursos, lista_equipos, lista_formaPago, lista_meses, lista_paquetes, lista_sesiones, lista_semanas

from ..utils.utils import allowed_file, get_db_connection, my_random_string, paginador3, sanitize_filename
from .routes import participantes

from supabase import create_client
import io
import urllib.parse

SUPABASE_URL = "https://ipecmsarkhzdzkkanxvj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlwZWNtc2Fya2h6ZHpra2FueHZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3MjY4ODAsImV4cCI6MjA2OTMwMjg4MH0.dy4dSDzoTifaRTU-wQnl6oju1iiYdxHN-p0kBbYU1lI"
BUCKET_NAME = "tickets"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

con = get_db_connection()
cur = con.cursor()

cur.execute('''
    SELECT id_sesion, fecha_curso, categoria
    FROM public.detalles_sesiones;
''')
sesiones = cur.fetchall()

hoy = date.today()

# Filtrar solo los que tienen categoria 1 y fecha pasada
ids_para_actualizar = [
    s[0] for s in sesiones
    if s[2] == 1 and s[1] < hoy
]

if ids_para_actualizar:
    cur.execute('''
                    UPDATE public.sesiones_curso
                    SET categoria = 6
                    WHERE id_sesion = ANY(%s);
                ''', (ids_para_actualizar,))

con.commit()
cur.close()
con.close()

#---------------------------------------------------------------PARTICIPANTES--------------------------------------------------------------------------
    
@participantes.route("/participantes/especializaciones_pasadas")
@login_required
def participantes_especializacionP_buscar():
    search_query = request.args.get('buscar', '', type=str).strip()
    search_query_sql = f"%{search_query}%"

    fecha_inicio_str = request.args.get('fecha_inicio', '', type=str)
    fecha_fin_str = request.args.get('fecha_fin', '', type=str)

    fecha_inicio = None
    fecha_fin = None
    try:
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
    except ValueError:
        flash("Fechas inválidas", "warning")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT clave_participante FROM participantes ORDER BY id_participante DESC LIMIT 1")
    ultima_clave = cur.fetchone()
    cur.close()
    conn.close()

    clave_anterior = ultima_clave[0] if ultima_clave else ''

    # Construcción dinámica del WHERE
    condiciones = [
        "(v.nombre_participante ILIKE %s OR v.clave_participante ILIKE %s)",
        "v.nombre_categoria = 'Esp. Pasadas'"
    ]
    valores = [search_query_sql, search_query_sql]

    if fecha_inicio:
        condiciones.append("p.fecha_registro >= %s")
        valores.append(fecha_inicio)
    if fecha_fin:
        condiciones.append("p.fecha_registro <= %s")
        valores.append(fecha_fin)

    where_sql = " AND ".join(condiciones)

    sql_count = f"""
        SELECT COUNT(*) 
        FROM asistencias_detalladas v
        JOIN participantes p ON v.id_participante = p.id_participante
        WHERE {where_sql}
    """

    sql_lim = f"""
        SELECT v.*, p.fecha_registro
        FROM asistencias_detalladas v
        JOIN participantes p ON v.id_participante = p.id_participante
        WHERE {where_sql}
        ORDER BY v.id_participante DESC
        LIMIT %s OFFSET %s
    """

    paginado = paginador3(sql_count, sql_lim, tuple(valores), 1, 50)

    return render_template(
        'participantes/participantes_especializaciones_pasadas.html',
        clave_anterior=clave_anterior,
        formas=lista_formaPago(),
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
        search_query=search_query
    )
    
@participantes.route("/participantes/especializaciones_pasadas/filtros")
@login_required
def participantes_especializacionesP_filtros():
    equipos = request.args.get('equipos', '', type=str)
    fecha_raw = request.args.get('fecha', '', type=str)

    fecha_inicio_str = request.args.get('fecha_inicio', '', type=str)
    fecha_fin_str = request.args.get('fecha_fin', '', type=str)

    fecha_inicio = None
    fecha_fin = None
    try:
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
    except ValueError:
        flash("Fechas inválidas", "warning")

    cursos = ''
    equipo = ''
    if fecha_raw:
        partes = fecha_raw.split('/')
        if len(partes) == 3:
            cursos = partes[2]

    if equipos:
        partesEquipos = equipos.split(',')
        if len(partesEquipos) == 2:
            equipo = partesEquipos[1]

    # Construcción dinámica
    condiciones = [
        "(%s = '' OR v.nombre_equipo ILIKE %s)",
        "(%s = '' OR v.nombre_curso ILIKE %s)",
        "v.nombre_categoria = 'Esp. Pasadas'"
    ]
    valores = [equipo, equipo, cursos, cursos]

    if fecha_inicio:
        condiciones.append("p.fecha_registro >= %s")
        valores.append(fecha_inicio)
    if fecha_fin:
        condiciones.append("p.fecha_registro <= %s")
        valores.append(fecha_fin)

    where_sql = " AND ".join(condiciones)

    sql_count = f"""
        SELECT COUNT(*) 
        FROM asistencias_detalladas v
        JOIN participantes p ON v.id_participante = p.id_participante
        WHERE {where_sql}
    """

    sql_lim = f"""
        SELECT v.*, p.fecha_registro
        FROM asistencias_detalladas v
        JOIN participantes p ON v.id_participante = p.id_participante
        WHERE {where_sql}
        ORDER BY v.nombre_participante DESC
        LIMIT %s OFFSET %s
    """

    paginado = paginador3(sql_count, sql_lim, tuple(valores), 1, 50)

    return render_template(
        'participantes/participantes_especializaciones_pasadas.html',
        formas=lista_formaPago(),
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
        total_pages=paginado[4]
    )

#-----------------------------------------------------------------------------------------

@participantes.route("/participantesEP/agregar")
@login_required
def participante_agregarEP():
    return render_template('participantes/participantes_agregar.html',
                           formas = lista_formaPago(),
                           cursos = lista_cursos(),
                           sesiones = lista_sesiones(),
                           cuentas = lista_cuentas(),
                           paquetes = lista_paquetes())

@participantes.route('/participantesEP/agregar/nuevo', methods=('GET', 'POST'))
@login_required
def participante_nuevoEP():

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
        fecha_registro = datetime.now()

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
            (nombre_participante,apellidos_participante, num_telefono, clave_participante, nombre_paquete, nombre_empleado, estado, equipos, fecha_registro, forma_pago, cuenta_destino )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_participante
        '''
        valores = (nombre_participante,apellidos_participante, num_telefono, clave_participante, nombre_paquete, nombre_empleado, estado, equipos, fecha_registro, 1, 1)
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
        return redirect(url_for('participantes.participantes_especializacionP_buscar',
                                mes=request.form.get('mes', ''),
                                semana=request.form.get('semana', ''),
                                fecha=request.form.get('fecha', ''),
                                equipos=equipos))
#---------------------------------------------------------------------------------------------------------------
def to_bool(value):
    return value in [1, '1', True, 'true', 'True']
#---------------------------------------------------------------------------------------------------------------
@participantes.route('/participantesEP/actualizar/<int:id>', methods=['POST'])
@login_required
def actualizar_participanteEP(id):
    datos = request.get_json()

    con = get_db_connection()
    cur = con.cursor()
    ingresos = datos.get('ingresos')
    factura_pago = to_bool(datos.get('factura_pago'))
    confirmacion_grupo = to_bool(datos.get('confirmacion_grupo'))
    materiales = to_bool(datos.get('materiales'))
    grabaciones = to_bool(datos.get('grabaciones'))
    evaluacion_dc3 = to_bool(datos.get('evaluacion_dc3'))

    try:
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
            datos['num_telefono'],
            datos['nombre_participante'],
            datos['apellidos_participante'],
            datos['nombre_paquete'],
            datos['fecha_pago'] or None,
            factura_pago,
            datos['cuenta_destino'],
            confirmacion_grupo,
            materiales,
            grabaciones,
            evaluacion_dc3,
            datos['observaciones'],
            id
        )
        cur.execute(sql_participante, valores)

        # ------------------- Actualiza tabla pagos -------------------
        if 'ingresos' in datos:
            ingresos = float(datos['ingresos'])
            sql_pago = '''
                UPDATE pagos
                SET ingresos = %s,
                    fecha_pago = %s
                WHERE participante = %s
            '''
            cur.execute(sql_pago, (
                ingresos,
                datos['fecha_pago'] or None,
                id
            ))
        else:
            sql_pago = '''
                UPDATE pagos
                SET fecha_pago = %s
                WHERE participante = %s
            '''
            cur.execute(sql_pago, (
                datos['fecha_pago'] or None,
                id
            ))


        con.commit()
        return jsonify({'alert': 'Participante actualizado correctamente'})

    except Exception as e:
        con.rollback()
        print(f'Error al actualizar participante: {e}')  # <-- AGREGA ESTO
        return jsonify({'alert': f'Error al actualizar participante: {e}'}), 500
    finally:
        cur.close()
        con.close()

@participantes.route('/participantesEP/actualizar/sesion/<string:id>', methods=['POST'])
@login_required
def participante_actualizarEP(id):
    sesion = request.form['sesion']
    grabacion = request.form.get('grabacion')  # None si no existe

    grabacion_new = True if grabacion == 'on' else False

    con = get_db_connection()
    cur = con.cursor()

    cur.execute(
        "UPDATE asistencias SET sesion = %s WHERE participante = %s",
        (sesion, id)
    )

    cur.execute(
        "UPDATE participantes SET grabacion = %s WHERE id_participante = %s",
        (grabacion_new, id)
    )

    con.commit()
    cur.close()
    con.close()

    flash("Participante cambiado de sesión")
    return redirect(url_for('participantes.participantes_especializacionP_buscar'))

@participantes.route('/participantesEP/comprobante/<string:id>', methods=['POST'])
@login_required
def participante_comprobanteEP(id):
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

    # Actualiza pagos
    sql1 = '''UPDATE pagos SET forma_pago = %s WHERE participante = %s'''
    cur.execute(sql1, (forma_pago, id))

    # Actualiza participante
    sql2 = '''UPDATE participantes SET cuenta_destino = %s, forma_pago = %s WHERE id_participante = %s'''
    cur.execute(sql2, (cuenta_destino, forma_pago, id))

    # Sanitizar clave para carpeta
    clave_segura = sanitize_filename(clave_participante)

    for imagen in imagenes:
        if imagen and allowed_file(imagen.filename):
            cadena_aleatoria = my_random_string()

            # Crear nombre seguro para el archivo
            nombre_archivo = f"{nombre_participante}_{apellidos_participante}_{clave_participante}_{creado.strftime('%Y-%m-%d')}_{cadena_aleatoria}_{secure_filename(imagen.filename)}"
            nombre_archivo = sanitize_filename(nombre_archivo)

            imagen_bytes = imagen.read()

            path_remoto = f"{clave_segura}/{nombre_archivo}"

            # Subir a Supabase
            supabase.storage.from_(BUCKET_NAME).upload(
                path_remoto,
                imagen_bytes,
                file_options={"content-type": imagen.content_type}
            )

            # Registrar en DB
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
    return redirect(url_for('participantes.participantes_especializacionP_buscar'))