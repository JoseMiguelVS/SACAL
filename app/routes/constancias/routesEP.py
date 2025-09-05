from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor
from flask import send_file
from io import BytesIO

from .generador import generar_constancia
from .qr import generar_qr_memoria
from app.utils.listas import lista_categorias, lista_cuentas, lista_cursos, lista_equipos, lista_meses, lista_paquetes, lista_ponente, lista_privilegios, lista_semanas, lista_sesiones

from ..utils.utils import get_db_connection, paginador1, paginador2, paginador3

from .routes import constancias

#-----------------------------------------PRINCIPAL-------------------------------------------------
@constancias.route("/constancias_espPasadas")
@login_required
def constancias_espPasadas():
    search_query = request.args.get('buscar', '', type=str).strip()
    search_query_sql = f"%{search_query}%"

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas_constancias
                   WHERE (nombre_participante ILIKE %s OR clave_participante ILIKE %s) AND (validacion_pago = 1 OR validacion_pago = 2)
                   AND constancia_enviada = False AND nombre_categoria = 'Esp. Pasadas' '''

    sql_lim = '''SELECT * FROM asistencias_detalladas_constancias
                 WHERE (nombre_participante ILIKE %s OR clave_participante ILIKE %s) AND (validacion_pago = 1 OR validacion_pago = 2)
                 AND constancia_enviada =  AND nombre_categoria = 'Esp. Pasadas' 
                 ORDER BY nombre_participante DESC
                 LIMIT %s OFFSET %s'''

    # Ejecutar el conteo de constancias no enviadas
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT COUNT(*) 
        FROM asistencias_detalladas_constancias 
        WHERE constancia_enviada = False AND (validacion_pago = %s OR validacion_pago = %s)
    ''', (1, 2))    

    constancias_por_enviar = cur.fetchone()[0]
    cur.close()
    conn.close()

    paginado = paginador3(sql_count, sql_lim, [search_query_sql, search_query_sql], 1, 25)

    return render_template('constancias/constancias_espPasadas.html',
                           equipos=lista_equipos(),
                           categorias=lista_categorias(),
                           cursos=lista_cursos(),
                           sesiones=lista_sesiones(),
                           paquetes=lista_paquetes(),
                           cuentas=lista_cuentas(),
                           privilegios=lista_privilegios(),
                           meses=lista_meses(),
                           semanas=lista_semanas(),
                           constancias=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query,
                           constancias_por_enviar=constancias_por_enviar)

@constancias.route("/constancias_espPasadas/filtros") 
@login_required
def constancias_espPasadas_filtros():
    # search_query = request.args.get('buscar', '', type=str)
    nombre_mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)
    fecha_raw = request.args.get('fecha', '', type=str)

    fecha_curso = ''
    if fecha_raw:
        partes = fecha_raw.split('/')
        if len(partes) == 3:
            fecha = partes[1]  # parte central es la fecha

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas_constancias
                WHERE (%s = '' OR nombre_mes ILIKE %s)
                    AND (%s = '' OR semana ILIKE %s)
                AND constancia_enviada = False  AND nombre_categoria = 'Esp. Pasadas' '''

    sql_lim = '''SELECT * FROM asistencias_detalladas_constancias
            WHERE (%s = '' OR nombre_mes ILIKE %s)
                AND (%s = '' OR semana ILIKE %s)
                AND constancia_enviada = False AND nombre_categoria = 'Esp. Pasadas' 
            ORDER BY nombre_participante DESC
            LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [
            nombre_mes, nombre_mes, 
            semana, semana, 
            # search_query, search_query, search_query
        ],
        1, 25
    )

    return render_template('constancias/constancias_espPasadas.html',
                           equipos=lista_equipos(),
                           categorias=lista_categorias(),
                           cursos=lista_cursos(),
                           sesiones=lista_sesiones(),
                           paquetes=lista_paquetes(),
                           cuentas=lista_cuentas(),
                           privilegios=lista_privilegios(),
                           meses=lista_meses(),
                           semanas=lista_semanas(),
                           constancias=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4])

#------------------------------------------------------DETALLES-----------------------------------------------------
@constancias.route("/constancias_espPasadas/detalles/<int:id>")
@login_required
def constancias_espPasadas_detalles(id):
     with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM datos_constancias1 WHERE id_participante = %s',(id,))
            participantes = cur.fetchone()
        if participantes is None:
            flash('El participante no exite o ha sido eliminado.')
            return redirect(url_for('constancias.constancias_espPasadas'))
        return render_template('constancias/constancias_espPasadas_detalles.html', 
                               participantes = participantes)
     
#----------------------------------------------------------GENERADOR DE CONSTANCIAS-------------------------------------------------------------
@constancias.route('/constancias_espPasadas/folio/', methods=["POST"])
@login_required
def folio_constancia():
    folio = request.form.get("folio_constancia")
    id = request.args.get("id")
    curso = request.args.get("curso")
    fecha_curso = request.args.get("fecha_curso")  # formato ISO: 'YYYY-MM-DD'

    if not id or not curso or not fecha_curso or not folio:
        flash('Datos incompletos', 'Error')
        return redirect(url_for('constancias.constancias_espPasadas'))

    with get_db_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                UPDATE constancias
                SET folio_constancia = %s
                WHERE participante = %s
            """, (folio, id))
            con.commit()

    # Redirigir a la generación automática de constancia
    return redirect(url_for(
    'constancias.constancias_generar',
    id=id,
    curso=curso,
    fecha_curso=fecha_curso
))

# ------------------------------------FOLIO DEL PARTICIPANTE------------------------------------
@constancias.route("/constancias_espPasadas/folio/generar")
@login_required 
def constancias_espPasadas_generar():
    id = request.args.get("id")
    curso = request.args.get("curso")
    fecha_curso = request.args.get("fecha_curso")  # formato ISO: 'YYYY-MM-DD'

    if not id or not curso or not fecha_curso:
        flash('Datos incompletos')
        return redirect(url_for('constancias.constancias_espPasadas'))

    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM datos_constancias1
                WHERE id_participante = %s AND nombre_curso = %s AND fecha_curso = %s
            """, (id, curso, fecha_curso))
            participante = cur.fetchone()
            if not participante:
                return "Constancia no encontrada", 404

        qr_buffer = generar_qr_memoria(participante)
        pdf_buffer, nombre_archivo = generar_constancia(participante, qr_path=qr_buffer)

        with con.cursor() as cur:
            cur.execute("""
                UPDATE constancias
                SET constancia_generada = TRUE
                WHERE participante = %s
            """, (id,))
        con.commit()

    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nombre_archivo
    )

#--------------------------------------------------------------EDITAR PARTICIPANTE----------------------------------------------------------------------------
@constancias.route("/constancias_espPasadas/participantes")
@login_required
def constancias_espPasadas_editar():
    id = request.args.get("id")
    curso = request.args.get("curso")
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM asistencias_detalladas_constancias WHERE id_participante = %s AND nombre_curso = %s', (id, curso))
    participante = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('constancias/constancias_espPasadas_editar.html', 
                           participante = participante[0], 
                           cursos = lista_cursos(), 
                           categorias = lista_categorias(), 
                           ponentes = lista_ponente())

@constancias.route("/constancias_espPasadas/actualizar/<int:id>", methods = ['POST'])
@login_required
def constancias_espPasadas_actualizar(id):
    datos = request.form
    con = get_db_connection()
    cur = con.cursor()

    sql = '''
        UPDATE participantes SET
            clave_participante = %s,
            nombre_participante = %s,
            apellidos_participante = %s
        WHERE id_participante = %s
    '''
    valores = (
        datos['clave_participante'],
        datos['nombre_participante'],
        datos['apellidos_participante'],
        id
    )

    cur.execute(sql, valores)
    con.commit()
    cur.close()
    con.close()
    flash('Datos para constancia actualizados correctamente')
    return redirect(url_for('constancias.constancias_espPasadas'))

#-----------------------------------------------------------------------------------------------------------------
@constancias.route('/constancias_espPasadas/modificar', methods=['POST'])
@login_required
def modificar_constancias_espPasadas():
    id_participante = request.args.get("id")
    constancia_enviada = True
    datos = request.form

    if not id_participante:
        flash("Faltan parámetros", "Error")
        return redirect(url_for("constancias.constancias_espPasadas"))

    con = get_db_connection()
    cur = con.cursor()

    sql = '''
        UPDATE constancias SET
            constancia_enviada = %s,
            fecha_envio = %s
        WHERE participante = %s 
    '''
    valores = (
        constancia_enviada,
        datos.get('fecha_envio'),
        id_participante,
    )

    try:
        cur.execute(sql, valores)
        con.commit()
        flash("Datos para constancia actualizados correctamente", "Éxito")
    except Exception as e:
        con.rollback()
        flash("Error al actualizar: " + str(e), "Error")
    finally:
        cur.close()
        con.close()

    return redirect(url_for("constancias.constancias_espPasadas"))