from flask import Blueprint, render_template, request, redirect, url_for, flash, Flask,make_response
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

from utils.listas import lista_rol

from ..utils.utils import get_db_connection, paginador1, allowed_username

# Definir Blueprint
empleados = Blueprint('empleados', __name__)

#--------------------------------BUSCAR EMPLEADO / CONSULTA INICIAL--------------------------------------
@empleados.route("/empleados")
@login_required
def empleadosBuscar():
    search_query = request.args.get('buscar', '', type=str)
    sql_count ='SELECT COUNT(*) FROM empleados WHERE estado = true AND (nombre_usuario ILIKE %s OR correo_empleado ILIKE %s);'
    sql_lim ='SELECT * FROM empleados WHERE estado = true AND (nombre_usuario ILIKE %s OR correo_empleado ILIKE %s) ORDER BY id_empleado DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count,sql_lim,search_query,1,5)
    return render_template('empleados/empleados.html',
                           roles=lista_rol(),
                           empleados=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query = search_query)

#---------------------------------------AGREGAR EMPLEADO--------------------------------------------------

@empleados.route("/empleados/agregar")
@login_required
def empleado_agregar():
    titulo = "Agregar empleado"
    return render_template('empleados/empleados_agregar.html',titulo = titulo, roles=lista_rol())

@empleados.route("/empleados/agregar/nuevo", methods=('GET', 'POST'))
@login_required
def empleado_nuevo():
    if request.method == 'POST':
        nombre_usuario= request.form['nombre_usuario']
        if allowed_username(nombre_usuario):
            nombre_empleado = request.form['nombre_empleado']
            apellido_pat = request.form['apellido_pat']
            apellido_mat = request.form['apellido_mat']
            correo_empleado = request.form['correo_empleado']
            rol = request.form['id_rol']
            contrasenia_empleado = request.form['contrasenia_empleado']
            Pass = generate_password_hash(contrasenia_empleado)
            estado = True
            fecha_creacion= datetime.now()
            fecha_modificacion = datetime.now()
            
            con = get_db_connection()
            cur = con.cursor(cursor_factory=RealDictCursor)
            sql_validar="SELECT COUNT(*) FROM empleados WHERE correo_empleado = %s"
            cur.execute(sql_validar, (correo_empleado,))
            existe = cur.fetchone()['count']
            if existe:
                cur.close()
                con.close()
                flash('Error: El correo seleccionado ya esta registrado. Intente con uno diferente')
                return redirect(url_for('empleados.empleado_agregar'))
            else:
                sql="INSERT INTO empleados (nombre_empleado, apellido_mat, apellido_pat, nombre_usuario, correo_empleado, rol, estado, fecha_creacion, fecha_modificacion, contrasenia_empleado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s, %s, %s)"
                valores=(nombre_empleado, nombre_usuario, apellido_mat, apellido_pat, correo_empleado, rol, estado, fecha_creacion, fecha_modificacion, Pass)
                cur.execute(sql,valores)
                con.commit()
                cur.close()
                con.close()
                flash('Empleado agregado correctamente')
                return redirect(url_for('empleados.empleadosBuscar'))
            
        else:
            flash('Error: El correo no cuenta con las caracteristicas')
            return redirect(url_for('empleados.empleado_agregar'))
    return redirect(url_for('empleados.empleado_agregar'))

#-----------------------------DETALLES DE EMPLEADO-------------------------------

@empleados.route('/empleados/detalles/<int:id>')
@login_required
def empleado_detalles(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM empleados WHERE id_empleado = %s', (id,))  #generar vista para roles
            empleado = cur.fetchone()  # Recupera solo un registro
    if empleado is None:
        flash('El empleado no existe o ha sido eliminado.')
        return redirect(url_for('empleados.empleadosBuscar'))
    return render_template('empleados/empleado_detalles.html', empleado = empleado)

#-----------------------------------------EDITAR EMPLEADO----------------------------------
@empleados.route('/empleados/editar/<string:id>')
@login_required
def empleado_editar(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM empleados WHERE id_empleado={0}'.format(id))
    empleado = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return render_template('empleados/empleado_editar.html',empleado = empleado[0], roles = lista_rol())


@empleados.route('/empleados/editar/<string:id>',methods=['POST'])
@login_required
def empleado_actualizar(id):
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        nombre_empleado = request.form['nombre_empleado']
        apellido_mat = request.form['apellido_mat']
        apellido_pat = request.form['apellido_pat']
        correo_empleado = request.form['correo_empleado']
        rol = request.form['id_rol']
        fecha_modificacion= datetime.now()
        
        con = get_db_connection()
        cur = con.cursor()
        sql="UPDATE empleados SET nombre_usuario = %s ,nombre_empleado = %s, apellido_mat = %s, apellido_pat = %s, correo_empleado = %s, rol = %s, fecha_modificacion = %s WHERE id_empleado = %s"
        valores=(nombre_usuario, nombre_empleado,apellido_mat, apellido_pat, correo_empleado, rol, fecha_modificacion, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash("Empleado actualizado correctamente")
    return redirect(url_for('empleados.empleadosBuscar'))

#--------------------------------ELIMINAR EMPLEADO------------------------------

@empleados.route('/empleados/eliminar/<string:id>')
@login_required
def empleado_eliminar(id):
    estado = False
    fecha_modificacion = datetime.now()
    con = get_db_connection()
    cur = con.cursor()
    sql = "UPDATE empleados SET estado=%s,fecha_modificacion=%s WHERE id_empleado=%s"
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql,valores)
    con.commit()
    cur.close()
    con.close()
    flash("Empleado eliminado correctamente")
    return redirect(url_for('empleados.empleadosBuscar'))
# -----------------------------------------------------------PAPELERA DE EMPLEADO--------------------------------------------------------------------

@empleados.route("/empleados/papelera")
@login_required
def empleados_papelera():
    search_query = request.args.get('buscar', '', type=str)
    sql_count ='SELECT COUNT(*) FROM empleados WHERE estado = False AND (nombre_usuario ILIKE %s OR correo_empleado ILIKE %s);'
    sql_lim ='SELECT * FROM empleados WHERE estado = false AND (nombre_usuario ILIKE %s OR correo_empleado ILIKE %s) ORDER BY id_empleado DESC LIMIT %s OFFSET %s;'
    paginado = paginador1(sql_count,sql_lim,search_query,1,5)
    return render_template('empleados/empleados_papelera.html',
                           empleados=paginado[0],
                           page=paginado[1],
                           per_page=paginado[2],
                           total_items=paginado[3],
                           total_pages=paginado[4],
                           search_query = search_query)

#-----------------------------------------------DETALLES DE EMPLEADO ELIMINADO--------------------------------------------------

@empleados.route('/empleados/papelera/detalles/<int:id>')
@login_required
def empleado_detallesPapelera(id):
    with get_db_connection() as con:
        with con.cursor(cursor_factory=RealDictCursor) as cur:
            # Asegúrate de usar parámetros para evitar inyección SQL
            cur.execute('SELECT * FROM empleados WHERE id_empleado = %s', (id,))
            usuario = cur.fetchone()  # Recupera solo un registro
    if usuario is None:
        flash('El empleado no existe o ha sido eliminado.')
        return redirect(url_for('empleados.empleadosBuscar'))
    return render_template('empleados/empleado_detallesPapelera.html')

#----------------------------------------------RESTAURAR EMPLEADO-----------------------------------------

@empleados.route('/empleados/papelera/restaurar/<string:id>')
@login_required
def empleados_restaurar(id):
    estado = True
    fecha_modificacion = datetime.now()
    con = get_db_connection()
    cur = con.cursor()
    sql = "UPDATE empleados SET estado=%s,fecha_modificacion=%s WHERE id_empleado=%s"
    valores = (estado, fecha_modificacion, id)
    cur.execute(sql,valores)
    con.commit()
    cur.close()
    con.close()
    flash("Empleado restaurado correctamente")
    return redirect(url_for('empleados.empleadosBuscar'))