from flask import Blueprint, jsonify, render_template, request, redirect, send_file, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..constancias.generador import generar_constancia
from ..constancias.qr import generar_qr
from utils.listas import lista_categorias, lista_cuentas, lista_cursos, lista_paquetes, lista_ponente, lista_sesiones

from ..utils.utils import get_db_connection, paginador3

constancias = Blueprint('constancias', __name__)

@constancias.route("/constancias")
@login_required
def constancias_buscar():
    nombre_categoria = request.args.get('nombre_categoria', '', type=str)
    sesion = request.args.get('sesion', '', type=str)

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas_constancias
                   WHERE (%s = '' OR nombre_categoria::text = %s)
                     AND (%s = '' OR fecha ILIKE %s)'''

    sql_lim = '''SELECT * FROM asistencias_detalladas_constancias
                 WHERE (%s = '' OR nombre_categoria::text = %s)
                   AND (%s = '' OR fecha ILIKE %s)
                 ORDER BY nombre_participante DESC
                 LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [nombre_categoria, nombre_categoria, sesion, sesion],
        1, 20
    )

    return render_template('constancias/constancias.html',
                           categorias = lista_categorias(),
                           cursos=lista_cursos(),
                           sesiones = lista_sesiones(),
                           paquetes = lista_paquetes(),
                           cuentas = lista_cuentas(),
                           constancias=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4])

#------------------------------------------------------DETALLES-----------------------------------------------------

@constancias.route("/constancias/detalles/<int:id>")
@login_required
def constancias_detalles(id):
     with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM asistencias_detalladas WHERE id_participante = %s',(id,))
            participantes = cur.fetchone()
        if participantes is None:
            flash('El participante no exite o ha sido eliminado.')
            return redirect(url_for('constancias.constancias_buscar'))
        return render_template('constancias/constancias_detalles.html', 
                               participantes = participantes)
     
from flask import request

#----------------------------------------------------------GENERADOR DE CONSTANCIAS-------------------------------------------------------------

@constancias.route("/constancias/constancia")
@login_required
def constancias_generar():
    id = request.args.get("id")
    curso = request.args.get("curso")
    fecha = request.args.get("fecha")  # formato ISO: 'YYYY-MM-DD'

    if not id or not curso or not fecha:
        return "Datos incompletos", 400

    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM datos_constancias 
                WHERE id_participante = %s AND nombre_curso = %s AND fecha = %s
            """, (id, curso, fecha))
            participante = cur.fetchone()
            if not participante:
                return "Constancia no encontrada", 404

    qr_path = generar_qr(participante)
    pdf_path = generar_constancia(participante, qr_path)
    return send_file(pdf_path, as_attachment=True)

#--------------------------------------------------------------EDITAR PARTICIPANTE----------------------------------------------------------------------------
        
@constancias.route("/constancias/participantes/<int:id>")
@login_required
def constancias_editar(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM asistencias_detalladas_constancias WHERE id_participante={0}'.format(id))
    participante = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('constancias/constancias_editar.html', 
                           participante = participante[0], 
                           cursos = lista_cursos(), 
                           categoria = lista_categorias(), 
                           ponentes = lista_ponente())

@constancias.route("/constancias/actualizar/<int:id>", methods = ['POST'])
@login_required
def actualizar_participante(id):
    datos = request.get_json()
    con = get_db_connection()
    cur = con.cursor()

    sql = '''
        UPDATE participantes SET
            clave_participante = %s,
            nombre_participante = %s
        WHERE id_participante = %s
    '''
    valores = (
        datos['clave_participante'],
        datos['nombre_participante'],
        id
    )

    sql2 = '''
        UPDATE sesiones_curso SET
            nombre_curso = %s,
            horario_inicio = %s,
            horario_fin = %s,
            fecha = %s,
            categoria = %s,
            ponente = %s,
        WHERE id_participante = %s
    '''
    valores2 = (
        datos['nombre_curso'],
        datos['horario_inicio'],
        datos['horario_fin'],
        datos['fecha'],
        datos['categoria'],
        datos['ponente'],
        id
    )

    cur.execute(sql, valores, sql2, valores2)
    con.commit()
    cur.close()
    con.close()

    return jsonify({'message': 'Participante actualizado correctamente'})