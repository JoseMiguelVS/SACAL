from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from utils.listas import lista_categorias, lista_temas

from ..utils.utils import get_db_connection, paginador2, allowed_paquename

paquetes = Blueprint('paquete', __name__)

#-----------------------------BUSCAR PAQUETES / CONSULTA--------------------------
@paquetes.route("/paquetes")
@login_required
def paquetes_buscar():
    search_query = request.args.get('buscar', '', type = str).strip()

    if search_query:
        sql_count = 'SELECT COUNT(*) detalles_paquetes WHERE estado = True AND nombre_paquete ILIKE %s;'
        sql_lim = 'SELECT * FROM detalles_paquetes WHERE estado = True AND nombre_paquete ILIKE %s ORDER BY id_paquete DESC LIMIT %s OFFSET %s;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT(*) FROM detalles_paquetes WHERE estado = True;'
        sql_lim = 'SELECT * FROM detalles_paquetes WHERE estado = True ORDER BY id_paquete DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1 , 5)

    return render_template('paquetes/paquetes.html',
                           categorias = lista_categorias(),
                           temas = lista_temas(),
                           paquetes=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)

#------------------------AGREGAR PAQUETE---------------------------
@paquetes.route("/paquetes/agregar")
@login_required
def paquete_agregar():
    titulo = "Agregar paquete"
    return render_template('paquetes/paquetes_agregar.html', titulo = titulo, temas = lista_temas())


@paquetes.route("/paquetes/agregar/nuevo", methods=('GET', 'POST'))
@login_required
def paquete_nuevo():
    if request.method == 'POST':
        nombre_paquete = request.form['nombre_paquete']

        if allowed_paquename(nombre_paquete):
            precio_paquete = request.form['precio_paquete']
            categoria_paquete = request.form['id_categoria']
            estado = True
            fecha_creacion = datetime.now()
            fecha_modificacion = datetime.now()

            # Verificamos si el usuario marcó la casilla de regalos
            try:
                con = get_db_connection()
                cur = con.cursor(cursor_factory=RealDictCursor)

                # Insertar paquete y recuperar su ID
                sql='''
                        INSERT INTO paquetes (nombre_paquete, precio_paquete, categoria_paquete, estado, fecha_creacion, fecha_modificacion)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    '''
                valores = (nombre_paquete, precio_paquete, categoria_paquete, estado, fecha_creacion, fecha_modificacion)
                cur.execute(sql, valores)

                con.commit()
                flash('Paquete agregado correctamente')
                return redirect(url_for('paquete.paquetes_buscar'))

            except Exception as e:
                print("Error al insertar paquete:", e)
                con.rollback()
                flash('Error al registrar el paquete')
                return redirect(url_for('paquete.paquete_agregar'))

            finally:
                cur.close()
                con.close()

        else:
            flash('Nombre de paquete no válido')
            return redirect(url_for('paquete.paquete_agregar'))

    return redirect(url_for('paquete.paquete_agregar'))


#---------------------------------------DETALLES DE PAQUETE------------------------------
@paquetes.route('/paquetes/detalles/<int:id>')
@login_required
def paquete_detalles(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM detalles_paquetes WHERE id_paquete = %s', (id,))
            paquete = cur.fetchone()
    if paquete is None:
        flash('El paquete no existe o ha sido eliminado.')
        return redirect(url_for('paquete.paquete_buscar'))
    return render_template('paquetes/paquetes_detalles.html', paquete = paquete)

#------------------------------EDITAR PAQUETE---------------------------
@paquetes.route('/paquetes/editar/<string:id>')
@login_required
def paquete_editar(id):
    try:
        con = get_db_connection()
        cur = con.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM paquetes WHERE id_paquete = %s', (id,))
        paquete = cur.fetchone()
        cur.close()
        con.close()

        if not paquete:
            flash('Paquete no encontrado', 'danger')
            return redirect(url_for('paquete.paquetes_buscar'))

        return render_template('/paquetes/paquetes_editar.html', paquete=paquete, temas = lista_temas())

    except Exception as e:
        print(f"Error al cargar paquete: {e}")
        flash('Error al cargar el paquete', 'danger')
        return redirect(url_for('paquete.paquetes_buscar'))


@paquetes.route('/paquetes/editar/<string:id>', methods=['POST'])
@login_required
def paquete_actualizar(id):
    if request.method == 'POST':
        try:
            nombre_paquete = request.form['nombre_paquete']
            precio_paquete = request.form['precio_paquete']
            categoria_paquete = request.form['id_categoria']
            fecha_modificacion = datetime.now()

            con = get_db_connection()
            cur = con.cursor()
            sql = '''
                UPDATE paquetes
                SET nombre_paquete = %s,
                    precio_paquete = %s,
                    tem = %s,
                    fecha_modificacion = %s
                WHERE id_paquete = %s
            '''
            valores = (nombre_paquete, precio_paquete, categoria_paquete, fecha_modificacion, id)
            cur.execute(sql, valores)
            con.commit()
            cur.close()
            con.close()
            flash('Paquete actualizado correctamente', 'success')
        except Exception as e:
            print(f"Error al actualizar paquete: {e}")
            flash('Error al actualizar el paquete', 'danger')
            return redirect(url_for('paquete.paquete_editar', id=id))

    return redirect(url_for('paquete.paquetes_buscar'))


#-------------------------------ELIMINAR PAQUETES----------------------------
@paquetes.route('/paquetes/eliminar/<string:id>')
@login_required
def paquete_eliminar(id):
    estado = False
    fecha_modificacion = datetime.now()
    con = get_db_connection()
    cur = con.cursor()
    sql = 'UPDATE paquetes SET estado = %s, fecha_modificacion = %s WHERE id_paquete = %s;'
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql,valores)
    con.commit()
    cur.close()
    con.close()
    flash('Paquete eliminado correctamente')
    return redirect(url_for('paquete.paquetes_buscar'))

#-------------------------PAPELERA DE PAQUETES--------------------------
@paquetes.route("/paquetes/papelera")
@login_required
def paquetes_papelera():
    search_query = request.args.get('buscar', '', type = str).strip()

    if search_query:
        sql_count = 'SELECT COUNT(*) detalles_paquetes WHERE estado = False ADN nombre_paquete ILIKE %s;'
        sql_lim = 'SELECT * FROM detalles_paquetes WHERE estado = False AND nombre_paquete ILIKE %s ORDER BY id_paquete DESC LIMIT %s OFFSET;'
        params_count = (f"%{search_query}%",)
        params_lim = (f"%{search_query}%",)
    else:
        sql_count = 'SELECT COUNT(*) FROM detalles_paquetes WHERE estado = False;'
        sql_lim = 'SELECT * FROM detalles_paquetes WHERE estado = False ORDER BY id_paquete DESC LIMIT %s OFFSET %s;'
        params_count = ()
        params_lim = ()

    paginado = paginador2(sql_count, sql_lim, params_count, params_lim, 1 , 5)

    return render_template('paquetes/paquetes_papelera.html',
                           paquetes=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query=search_query)

#----------------------------------DETALLES DE PAQUETES ELIMINADO-----------------------------
@paquetes.route('/paquetes/papelera/detalles/<int:id>')
@login_required
def paquete_detallesPapelera(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM paquetes WHERE id_paquete = %s', (id))
            paquete = cur.fetchone()
    if paquete is None:
        flash('El paquete no existe o ha sido eliminado.')
        return redirect(url_for('paquetes.paquete_buscar'))
    return render_template('paquetes/paquete_detallesPapelera.html', paquete = paquete)

#------------------------------------RESTAURAR PAQUETE ------------------------------
@paquetes.route('/paquetes/papelera/restaurar/<string:id>')
@login_required
def paquete_restaurar(id):
    estado = True
    fecha_modificacion = datetime.now()
    con = get_db_connection()
    cur = con.cursor()
    sql = 'UPDATE paquetes SET estado = %s, fecha_modificacion = %s WHERE id_paquete = %s;'
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql,valores)
    con.commit()
    cur.close()
    con.close()
    flash('Paquete restaurado correctamente')
    return redirect(url_for('paquete.paquetes_buscar'))