from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..utils.utils import get_db_connection, paginador3

resumen_semanal = Blueprint('resumen_semanal', __name__)

#--------------------------------------------MAIN--------------------------------------------

@resumen_semanal.route('/resumen', methods=['GET'])
@login_required
def resumen():
    mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)

    sql = ''' 
                SELECT * FROM resumen_semanal
                WHERE (%(mes)s = '' OR nombre_mes ILIKE %(mes)s)
                AND (%(semana)s = '' OR semana ILIKE %(semana)s)
          '''
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)  # Aquí el cambio
    cur.execute(sql, {'mes': mes, 'semana': semana})
    resumen_datos = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('resumen/resumen.html', datos=resumen_datos, mes=mes, semana=semana)