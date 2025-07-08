from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash
from flask_login import login_required
from datetime import datetime
from psycopg2.extras import RealDictCursor

from ..utils.utils import get_db_connection, paginador3

resumen = Blueprint('resumen', __name__)

#--------------------------------------------MAIN--------------------------------------------

@resumen.route("/resumen")
@login_required
def resumen_filtros():
    mes = request.args.get('mes', '', type=str)
    semana = request.args.get('semana', '', type=str)

    cursos_ponentes='''
                        SELECT 
                    '''

    sql_count = '''
                    SELECT COUNT(*) FROM asistencias_detalladas_constancias
                    WHERE ingresos <> 0 or ingreso_factura <> 0
                    AND (%s = '' OR meses ILIKE %s )
                    AND (%s = '' OR semanas ILIKE %s )
                '''
    
    sql_lim = '''
                    SELECT * FROM asistencias_detalladas_constancias
                    WHERE ingresos <> 0 or ingreso_factura <> 0
                    AND (%s = '' OR meses ILIKE %s )
                    AND (%s = '' OR semanas ILIKE %s )
             '''
    
    paginado = paginador3(
        sql_count, sql_lim,
        [
            mes, mes,
            semana, semana
        ], 1, 5
        )