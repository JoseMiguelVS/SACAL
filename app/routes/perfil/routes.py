# routes/perfil.py
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from psycopg2.extras import RealDictCursor

from app.routes.utils.utils import get_db_connection

perfil = Blueprint('perfil', __name__)

# Página de visualización del perfil
@perfil.route('/perfil')
@login_required
def ver_perfil():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    sql = '''SELECT * FROM detalles_empleados WHERE id_empleado = %s;'''
    cursor.execute(sql, (current_user.id_empleado,))
    perfil = cursor.fetchone()
    conn.close()
    return render_template('perfil/perfil.html', perfil=perfil)

@perfil.route('/perfil/editar/<string:id>', methods = ['POST'])
@login_required
def actualizar_perfil(id):
    if request.method == 'POST':
        nombre_empleado = request.form['nombre_empleado']
        apellido_pat = request.form['apellido_pat']
        apellido_mat = request.form['apellido_mat']
        nombre_usuario = request.form['nombre_usuario']
        correo_empleado = request.form['correo_empleado']
        fecha_modificacion = datetime.now()

        con = get_db_connection()
        cur = con.cursor()
        sql='UPDATE empleados SET nombre_empleado = %s, apellido_pat = %s, apellido_mat = %s, nombre_usuario = %s, correo_empleado = %s, fecha_modificacion = %s WHERE id_empleado = %s'
        valores = (nombre_empleado, apellido_pat, apellido_mat, nombre_usuario, correo_empleado, fecha_modificacion, id)
        cur.execute(sql, valores)
        con.commit()
        cur.close()
        con.close()
        flash("Sus datos fueron actualizados correctamente")
    return redirect(url_for('perfil.ver_perfil'))
