from flask import Blueprint,render_template, request, redirect, url_for, flash
from flask_login import login_required
from psycopg2.extras import RealDictCursor

from app.utils.listas import lista_tiposCur

from ..utils.utils import get_db_connection, paginador2

temas = Blueprint('temas',__name__)

#------------------------------------------------BUSCAR TEMAS---------------------------------------
@temas.route('/cursos/temas')
@login_required
def temas_buscar():
    search_query = request.args.get('buscar', '', type = str)

    if search_query:
        sql_count = 'SELECT COUNT(*) FROM detalles_temas WHERE nombre_tema ILIKE %s; '
        sql_lim = 'SELECT * FROM detalles_temas WHERE nombre_tema ILIKE %s ORDER BY id_tema DESC LIMIT %s OFFSET %s;'
        params_count = (f"{search_query}%",)
        params_lim = (f"{search_query}%",)
    else:
        sql_count = 'SELECT COUNT(*) FROM detalles_temas'
        sql_lim = 'SELECT * FROM detalles_temas ORDER BY id_tema DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1, 5)

    return render_template('temas/temas.html',
                                tipos = lista_tiposCur(),
                                temas = paginado[0],
                                page = paginado[1],
                                per_page = paginado[2],
                                total_items = paginado[3],
                                total_pages = paginado[4],
                                search_query = search_query)
    
# ---------------------- AGREGAR TEMA ----------------------
@temas.route("/temas/agregar/nuevo", methods=['POST'])
@login_required
def tema_nuevo():
    if request.method == 'POST':
        nombre_tema = request.form['nombre_tema']
        tipo_id = request.form['tipo_id']

        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)

        sql_validar = 'SELECT COUNT(*) FROM temas_cursos WHERE nombre_tema = %s;'
        cur.execute(sql_validar, (nombre_tema,))
        existe = cur.fetchone()['count']

        if existe:
            cur.close()
            con.close()
            flash('Error: el tema ya está registrado. Intente con otro nombre.', 'danger')
        else:
            sql = 'INSERT INTO temas_cursos (nombre_tema, tipo_id) VALUES (%s, %s);'
            valores = (nombre_tema, tipo_id)
            cur.execute(sql, valores)
            con.commit()
            flash('Tema agregado correctamente.', 'success')

        cur.close()
        con.close()
        return redirect(url_for('temas.temas_buscar'))


# ---------------------------------- EDITAR TEMA (vista para cargar los datos en una página) ---------------------
@temas.route('/temas/editar/<string:id>')
@login_required
def tema_editar(id):
    con = get_db_connection()
    cur = con.cursor(cursor_factory=RealDictCursor)

    # Usar parámetros en lugar de format para evitar inyección SQL
    cur.execute('SELECT * FROM temas_cursos WHERE id_tema = %s;', (id,))
    tema = cur.fetchone()

    cur.close()
    con.close()

    if tema:
        return render_template('temas/tema_editar.html', tema=tema, tipos=lista_tiposCur())
    else:
        flash('Error: Tema no encontrado.', 'danger')
        return redirect(url_for('temas.temas_buscar'))


@temas.route('/temas/editar/<string:id>', methods=['POST', 'GET'])
@login_required
def tema_actualizar(id):
    if request.method == 'POST':
        nombre_tema = request.form['nombre_tema']
        tipo_id = request.form['id_tipo']

        con = get_db_connection()
        cur = con.cursor()
        sql = 'UPDATE temas_cursos SET nombre_tema = %s, tipo_id = %s WHERE id_tema = %s;'
        valores = (nombre_tema, tipo_id, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash('Tema actualizado correctamente.', 'success')

    return redirect(url_for('temas.temas_buscar'))

