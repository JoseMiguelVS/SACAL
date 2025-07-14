# routes/perfil.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from psycopg2.extras import RealDictCursor

from routes.utils.utils import get_db_connection

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