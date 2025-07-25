from app.routes.utils.utils import get_db_connection

#---------------------- FUNCIÓN GENÉRICA -------------------------
def listar_tabla(nombre_tabla: str, campo_orden: str):
    try:
        con = get_db_connection()
        cur = con.cursor()
        query = f"SELECT * FROM {nombre_tabla} ORDER BY {campo_orden} ASC"
        cur.execute(query)
        resultados = cur.fetchall()
        cur.close()
        con.close()
        return resultados
    except Exception as e:
        print(f"Error al consultar {nombre_tabla}: {e}")
        return []

#--------------------- FUNCIONES ESPECÍFICAS ---------------------
def lista_cuentas():
    return listar_tabla('cuentas', 'id_cuenta')

def lista_sesiones():
    return listar_tabla('detalles_sesiones', 'id_sesion')

def lista_cursos():
    return listar_tabla('cursos', 'id_curso')

def lista_semanas():
    return listar_tabla('semanas', 'id_semana')

def lista_meses():
    return listar_tabla('meses', 'id_mes')

def lista_paquetes():
    return listar_tabla('paquetes', 'id_paquete')

def lista_categorias():
    return listar_tabla('categorias', 'id_categoria')

def lista_rol():
    return listar_tabla('roles', 'id_roles')

def lista_tipos():
    return listar_tabla('tipo_cursos', 'id_tipo')

def lista_temas():
    return listar_tabla('temas_cursos', 'id_tema')

def lista_tiposCer():
    return listar_tabla('tipo_certificacion', 'id_tipo')

def lista_ponente():
    return listar_tabla('ponentes', 'id_ponentes')

def lista_tiposCur():
    return listar_tabla('tipo_cursos', 'id_tipo')

def lista_privilegios():
    return listar_tabla('paquetes_privilegios', 'id_paquete')

def lista_equipos():
    return listar_tabla('equipos', 'id_equipo')

def lista_participantes():
    return listar_tabla('participantes','id_participante')

def lista_formaPago():
    return listar_tabla('formas_pago', 'id_forma')

def lista_conceptos():
    return listar_tabla('tipo_concepto_factura', 'id_concepto')

def lista_gastos():
    return listar_tabla('tipos_gastos', 'id_tipos_gastos')