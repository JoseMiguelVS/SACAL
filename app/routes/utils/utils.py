import os
import psycopg2
import re
from psycopg2.extras import RealDictCursor
from flask import Flask, request

#--------------------------------CONEXION BD------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(host='localhost', 
                                dbname='SGCC', 
                                user=os.environ['db_username'], 
                                password=os.environ['db_password'])
        return conn
    except psycopg2.Error as error:
        print(f"Error de conexión: {error}")
        return None

#-----------------------------EMPLEADOS / USUARIOS
def allowed_username(nombre_usuario):
    # Define el patrón de la expresión regular para letras y números sin espacios ni caracteres especiales
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    # Comprueba si el nombre de usuario coincide con el patrón
    if pattern.match(nombre_usuario):
        return True
    else:
        return False
    
#------------------------------PONENTES---------------------------------
def allowed_pontname(nombre_ponente):
    # Define el patrón de la expresión regular para letras y números sin espacios ni caracteres especiales
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    # Comprueba si el nombre de usuario coincide con el patrón
    if pattern.match(nombre_ponente):
        return True
    else:
        return False
    
#------------------------------PONENTES--------------------------------------
def allowed_catname(nombre_categoria):
    # Define el patrón de la expresión regular para letras y números sin espacios ni caracteres especiales
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    # Comprueba si el nombre de usuario coincide con el patrón
    if pattern.match(nombre_categoria):
        return True
    else:
        return False

#---------------------------------PAGINADOR-------------------------
def paginador1(sql_count: str, sql_lim: str, search_query: str, in_page: int, per_pages: int) -> tuple[list[dict], int, int, int, int]:
    
# Obtener parámetros de paginación
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)

    # Validar los valores de entrada
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    offset = (page - 1) * per_page

    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Ejecutar consulta para contar el total de elementos que coinciden con la búsqueda
        cursor.execute(sql_count, (f"%{search_query}%",f"%{search_query}%"))
        total_items = cursor.fetchone()['count']

        # Ejecutar consulta para obtener elementos paginados que coinciden con la búsqueda
        cursor.execute(sql_lim, (f"%{search_query}%",f"%{search_query}%", per_page, offset))
        items = cursor.fetchall()

    except psycopg2.Error as e:
        print(f"Error en la base de datos: {e}")
        items = []
        total_items = 0
    finally:
        # Asegurar el cierre de la conexión
        cursor.close()
        conn.close()

    # Calcular el total de páginas
    total_pages = (total_items + per_page - 1) // per_page

    return items, page, per_page, total_items, total_pages