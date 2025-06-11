from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..constancias.generador import generar_constancia
from ..constancias.qr import generar_qr
from utils.listas import lista_categorias, lista_cuentas, lista_cursos, lista_meses, lista_paquetes, lista_ponente, lista_privilegios, lista_semanas, lista_sesiones

from ..utils.utils import get_db_connection, paginador3

constancias = Blueprint('constancias', __name__)

@constancias.route("/constancias") 
@login_required
def constancias_buscar():
    nombre_mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)
    fecha = request.args.get('fecha', '', type=str)  # Usar directamente el valor completo

    sql_count = '''
        SELECT COUNT(*) FROM asistencias_detalladas_constancias
        WHERE (%s = '' OR nombre_mes ILIKE %s)
          AND (%s = '' OR semana ILIKE %s)
          AND (%s = '' OR fecha ILIKE %s) 
          AND constancia_enviada = False
    '''

    sql_lim = '''
        SELECT * FROM asistencias_detalladas_constancias
        WHERE (%s = '' OR nombre_mes ILIKE %s)
          AND (%s = '' OR semana ILIKE %s)
          AND (%s = '' OR fecha ILIKE %s) 
          AND constancia_enviada = False
        ORDER BY nombre_participante DESC
        LIMIT %s OFFSET %s
    '''

    paginado = paginador3(
        sql_count, sql_lim,
        [nombre_mes, nombre_mes, semana, semana, fecha, fecha],
        1, 50
    )

    return render_template('constancias/constancias.html',
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

@constancias.route("/constancias/detalles/<int:id>")
@login_required
def constancias_detalles(id):
     with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM datos_constancias WHERE id_participante = %s',(id,))
            participantes = cur.fetchone()
        if participantes is None:
            flash('El participante no exite o ha sido eliminado.')
            return redirect(url_for('constancias.constancias_buscar'))
        return render_template('constancias/constancias_detalles.html', 
                               participantes = participantes)
     
#----------------------------------------------------------GENERADOR DE CONSTANCIAS-------------------------------------------------------------

@constancias.route('/constancias/folio/', methods=["POST"])
@login_required
def folio_constancia():
    folio = request.form.get("folio_constancia")
    id = request.args.get("id")
    curso = request.args.get("curso")
    fecha = request.args.get("fecha")  # formato ISO: 'YYYY-MM-DD'

    if not id or not curso or not fecha or not folio:
        flash('Datos incompletos', 'Error')
        return redirect(url_for('constancias.constancias_buscar'))

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
    fecha=fecha
))


@constancias.route("/constancias/folio/generar")
@login_required 
def constancias_generar():
    id = request.args.get("id")
    curso = request.args.get("curso")
    fecha = request.args.get("fecha")  # formato ISO: 'YYYY-MM-DD'

    if not id or not curso or not fecha:
        flash('Datos incompletos')
        return redirect(url_for('constancias.constancias_buscar'))

    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Obtener datos
            cur.execute("""
                SELECT * FROM datos_constancias 
                WHERE id_participante = %s AND nombre_curso = %s AND fecha = %s
            """, (id, curso, fecha))
            participante = cur.fetchone()
            if not participante:
                return "Constancia no encontrada", 404

        # Generar QR y PDF
        qr_path = generar_qr(participante)
        pdf_path = generar_constancia(participante, qr_path)

        # Actualizar campo constancia_generada
        with con.cursor() as cur:
            cur.execute("""
                UPDATE constancias
                SET constancia_generada = TRUE
                WHERE participante = %s
            """, (id,))
        con.commit()

    return send_file(pdf_path, as_attachment=True)

#--------------------------------------------------------------EDITAR PARTICIPANTE----------------------------------------------------------------------------
        
@constancias.route("/constancias/participantes")
@login_required
def constancias_editar():
    id = request.args.get("id")
    curso = request.args.get("curso")
    fecha = request.args.get("fecha")
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM asistencias_detalladas_constancias WHERE id_participante = %s AND nombre_curso = %s AND fecha = %s', (id, curso, fecha))
    participante = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('constancias/constancias_editar.html', 
                           participante = participante[0], 
                           cursos = lista_cursos(), 
                           categorias = lista_categorias(), 
                           ponentes = lista_ponente())

@constancias.route("/constancias/actualizar/<int:id>", methods = ['POST'])
@login_required
def constancias_actualizar(id):
    datos = request.form
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
            horario_inicio = %s,
            horario_fin = %s,
            fecha = %s,
            categoria = %s
        WHERE id_sesion = %s
    '''
    valores2 = (
        datos['horario_inicio'],
        datos['horario_fin'],
        datos['fecha'],
        datos['id_categoria'],
        id
    )

    cur.execute(sql, valores)
    cur.execute(sql2, valores2)
    con.commit()
    cur.close()
    con.close()
    flash('Datos para constancia actualizados correctamente')
    return redirect(url_for('constancias.constancias_buscar'))

#-----------------------------------------------------------------------------------------------------------------
@constancias.route('/constancias/modificar', methods=['POST'])
@login_required
def modificar_constancia():
    id_participante = request.args.get("id")
    constancia_enviada = True
    datos = request.form  # ⚠️ Usamos form en lugar de get_json porque no será fetch

    if not id_participante:
        flash("Faltan parámetros", "Error")
        return redirect(url_for("constancias.constancias_buscar"))

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

    return redirect(url_for("constancias.constancias_buscar"))

#----------------------------------------------------------------------------------------------------------------------------------
@constancias.route("/constancias/hechas&enviadas")
@login_required
def constancias_hechas():
    nombre_categoria = request.args.get('nombre_categoria', '', type=str)
    sesion = request.args.get('sesion', '', type=str)

    sql_count = '''SELECT COUNT(*) FROM asistencias_detalladas_constancias
                   WHERE (%s = '' OR nombre_categoria::text = %s)
                     AND (%s = '' OR fecha ILIKE %s) AND constancia_enviada = true'''

    sql_lim = '''SELECT * FROM asistencias_detalladas_constancias
                 WHERE (%s = '' OR nombre_categoria::text = %s)
                   AND (%s = '' OR fecha ILIKE %s) AND constancia_enviada = true
                 ORDER BY nombre_participante DESC
                 LIMIT %s OFFSET %s'''

    paginado = paginador3(
        sql_count, sql_lim,
        [nombre_categoria, nombre_categoria, sesion, sesion],
        1, 20
    )

    return render_template('constancias/constancias_hechas.html',
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