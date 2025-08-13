import os
import uuid
import psycopg2
import re
from flask import redirect, url_for, flash
from flask_login import current_user
from functools import wraps
from psycopg2.extras import RealDictCursor
from flask import Flask, request
from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2

import unicodedata
import re

from datetime import date, timedelta

def lista_semanas_resumen(year=None):
    """
    Genera una lista de semanas para un año dado.
    Cada semana es una tupla (id, texto), donde texto es "DD MMM - DD MMM".
    Si no se especifica año, usa el actual.
    """
    if year is None:
        year = date.today().year

    # Encontrar el primer lunes del año (o el lunes antes del 1ro de enero)
    d = date(year, 1, 1)
    # Ajustamos a el lunes más cercano igual o anterior al 1 de enero
    d -= timedelta(days=d.weekday())

    semanas = []
    semana_id = 1

    while d.year <= year:
        inicio = d
        fin = d + timedelta(days=6)
        if inicio.year > year:
            break
        texto = f"{inicio.day:02d} {inicio.strftime('%b')} - {fin.day:02d} {fin.strftime('%b')}"
        semanas.append((semana_id, texto))
        semana_id += 1
        d += timedelta(weeks=1)

    return semanas

def sanitize_filename(filename):
    # Eliminar acentos y caracteres no ASCII
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    # Reemplazar espacios con guiones bajos
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^A-Za-z0-9._/-]', '', filename)
    return filename

#--------------------------------CONEXION BD------------------------
# def get_db_connection():
#     try:
#         conn = psycopg2.connect(
#             host=os.environ.get('db_host'),
#             dbname=os.environ.get('db_name'),
#             user=os.environ.get('db_username'),
#             password=os.environ.get('db_password')
#         )
#         return conn
#     except psycopg2.Error as error:
#         print(f"Error de conexión: {error}")
#         return None

DATABASE_URL = "postgresql://sacal_user:fkCuAuxYUAyzAg8OPB0HcDxyMFJI35qm@dpg-d1t6h049c44c73d6jmj0-a.oregon-postgres.render.com/sacal"
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

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
    
#------------------------------PAQUETES--------------------------------------
def allowed_paquename(nombre_paquete):
    # Define el patrón de la expresión regular para letras y números sin espacios ni caracteres especiales
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    # Comprueba si el nombre de usuario coincide con el patrón
    if pattern.match(nombre_paquete):
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

#---------------------------------PAGINADOR 2-------------------------
def paginador2(sql_count: str, sql_lim: str, params_count: tuple, params_lim: tuple, in_page: int, per_pages: int) -> tuple[list[dict], int, int, int, int]:
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    offset = (page - 1) * per_page

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Ejecutar consulta para contar total de elementos
        cursor.execute(sql_count, params_count)
        total_items = cursor.fetchone()['count']

        # Ejecutar consulta paginada
        cursor.execute(sql_lim, params_lim + (per_page, offset))
        items = cursor.fetchall()

    except psycopg2.Error as e:
        print(f"Error en la base de datos: {e}")
        items = []
        total_items = 0
    finally:
        cursor.close()
        conn.close()

    total_pages = (total_items + per_page - 1) // per_page

    return items, page, per_page, total_items, total_pages

#--------------------------------PAGINADOR 3------------------------
def paginador3(sql_count: str, sql_lim: str, filtros: list, in_page: int, per_pages: int) -> tuple:
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1
    offset = (page - 1) * per_page

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(sql_count, filtros)
        total_items = cursor.fetchone()['count']

        cursor.execute(sql_lim, filtros + [per_page, offset])
        items = cursor.fetchall()
    
    except Exception as e:
        print(f"Error en la base de datos: {e}")
        items = []
        total_items = 0
    finally:
        cursor.close()
        conn.close()

    total_pages = (total_items + per_page - 1) // per_page
    return items, page, per_page, total_items, total_pages

# --------------------------------------------------------------IMAGENES--------------------------------------------------------------

def my_random_string(string_length=10):
    """Regresa una cadena aleatoria de la longitud de string_length."""
    random = str(uuid.uuid4()) # Conviente el formato UUID a una cadena de Python.
    random = random.upper() # Hace todos los caracteres mayusculas.
    random = random.replace("-","") # remueve el separador UUID '-'.
    return random[0:string_length] # regresa la cadena aleatoria.

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def rol_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.rol != 1:  # Asumiendo que el rol "1" es el de administrador
            flash('No tienes permisos para acceder a esta sección.')
            return redirect(url_for('index'))  # O redirige a donde desees
        return f(*args, **kwargs)
    return decorated_function
