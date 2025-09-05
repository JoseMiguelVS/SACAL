from flask import Blueprint, render_template, request
from flask_login import login_required
from psycopg2.extras import RealDictCursor
from collections import defaultdict
from ..utils.utils import get_db_connection, rol_admin_required
from app.utils.listas import lista_categorias, lista_paquetes

resumen_semanal = Blueprint('resumen_semanal', __name__)

@resumen_semanal.route('/resumen', methods=['GET'])
@login_required
@rol_admin_required
def resumen():
    fecha_inicio_str = request.args.get('fecha_inicio', '', type=str)
    fecha_fin_str = request.args.get('fecha_fin', '', type=str)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Obtener cursos y su categoría
    query_cursos = "SELECT * FROM vista_gastos_detallados"
    params = []
    if fecha_inicio_str:
        query_cursos += " WHERE fecha_curso >= %s"
        params.append(fecha_inicio_str)
    if fecha_fin_str:
        query_cursos += " AND fecha_curso <= %s" if "WHERE" in query_cursos else " WHERE fecha_curso <= %s"
        params.append(fecha_fin_str)
    cur.execute(query_cursos, params)
    registros = cur.fetchall()

    # Traer paquetes directamente de la base de datos
    cur.execute("""
        SELECT id_paquete, nombre_paquete, precio_paquete, categoria_paquete
        FROM paquetes
    """)
    todos_paquetes = cur.fetchall()  # lista de dicts gracias a RealDictCursor

    datos_finales = []
    for r in registros: 
        fila = {}
        fila['fecha_obj'] = r['fecha_curso']
        fila['nombre_curso'] = r['cursos']
        fila['nombre_ponente'] = r['ponentes']
        fila['categoria'] = int(r['categoria'])
        
        # Filtrar paquetes de la categoría del curso
        paquetes_categoria = [p for p in todos_paquetes if int(p['categoria_paquete']) == fila['categoria']]
        
        fila['paquetes'] = []
        fila['total_promesas'] = 0
        fila['total_pagados'] = 0
        fila['total_generado'] = 0.0

    for p in paquetes_categoria:
        # Contar participantes de ese curso y paquete
        cur.execute("""
            SELECT 
                COUNT(*) AS total_promesas,
                COUNT(*) FILTER (WHERE validacion_pago = 1) AS total_pagados
            FROM asistencias_detalladas
            WHERE cursos = %s AND nombre_paquete = %s
        """, (fila['nombre_curso'], p['nombre_paquete']))
        conteo = cur.fetchone()

        fila['paquetes'].append({
            'nombre_paquete': p['nombre_paquete'],
            'precio_paquete': float(p['precio_paquete']),
            'total_promesas': conteo['total_promesas'],
            'total_pagados': conteo['total_pagados']
        })

        fila['total_promesas'] += conteo['total_promesas']
        fila['total_pagados'] += conteo['total_pagados']
        fila['total_generado'] += conteo['total_pagados'] * float(p['precio_paquete'])

    # Gastos
    fila['publicidad'] = float(r.get('publicidad') or 0)
    fila['honorarios'] = float(r.get('honorarios') or 0)
    fila['iva'] = float(r.get('iva') or 0)
    fila['gasto_ponente'] = float(r.get('gasto_ponente') or 0)
    fila['diferencia'] = fila['total_generado'] - fila['publicidad'] - fila['honorarios'] - fila['iva'] - fila['gasto_ponente']

    datos_finales.append(fila)

    # Agrupar por categoría para la plantilla
    cursos_por_categoria = defaultdict(list)
    for fila in datos_finales:
        cursos_por_categoria[fila['categoria']].append(fila)

    # Totales generales
    suma_total = sum(f['total_generado'] for f in datos_finales)
    publicidad_total = sum(f['publicidad'] for f in datos_finales)
    honorarios_total = sum(f['honorarios'] for f in datos_finales)
    iva_total = sum(f['iva'] for f in datos_finales)
    sueldos_total = sum(f['gasto_ponente'] for f in datos_finales)
    total_gastos = publicidad_total + honorarios_total + iva_total + sueldos_total
    meta = 100000.0
    porcentaje = (suma_total / meta) * 100 if meta > 0 else 0
    ingreso_faltante = max(0, meta - suma_total)

    cur.close()
    conn.close()

    return render_template(
        'resumen/resumen.html',
        cursos_por_categoria=cursos_por_categoria,
        categorias=lista_categorias(),
        fecha_inicio=fecha_inicio_str,
        fecha_fin=fecha_fin_str,
        suma_total=suma_total,
        publicidad_total=publicidad_total,
        honorarios=honorarios_total,
        iva=iva_total,
        sueldos=sueldos_total,
        total_gastos=total_gastos,
        meta=meta,
        porcentaje=porcentaje,
        ingreso_faltante=ingreso_faltante
    )
