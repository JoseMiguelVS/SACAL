from flask import Flask, current_app, render_template, url_for, redirect, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect

from app.models.ModelUser import ModuleUser
from app.models.entities.user import User
from app.routes.utils.utils import get_db_connection

from datetime import datetime, date

# Importa tus Blueprints
from app.routes.empleados.routes import empleados
from app.routes.ponentes.routes import ponentes
from app.routes.categorias.routes import categorias
from app.routes.paquetes.routes import paquetes
from app.routes.cursos.routes import cursos
from app.routes.participantes.routes import participantes
from app.routes.sesiones.routes import sesiones
from app.routes.constancias.routes import constancias
from app.routes.temas.routes import temas
from app.routes.pagos.routes import pagos
from app.routes.resumen.routes import resumen_semanal
from app.routes.perfil.routes import perfil
from app.routes.participantes.routesE import participantes
from app.routes.participantes.routesEP import participantes
from app.routes.participantes.routesG import participantes
# -------------------------- Inicialización --------------------------
app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = 'secret'

# Login
login_manager = LoginManager(app)
login_manager.login_view = 'loguear'

@login_manager.user_loader
def load_user(idusuarios):
    return ModuleUser.get_by_id(get_db_connection(), idusuarios)

# Blueprints
app.register_blueprint(empleados)
app.register_blueprint(ponentes)
app.register_blueprint(categorias)
app.register_blueprint(paquetes)
app.register_blueprint(cursos)
app.register_blueprint(participantes)
app.register_blueprint(sesiones)
app.register_blueprint(temas)
app.register_blueprint(constancias)
app.register_blueprint(pagos)
app.register_blueprint(resumen_semanal)
app.register_blueprint(perfil)

# Carpeta temporal para almacenar comprobantes antes de subirlos a Supabase
app.config['UPLOAD_FOLDER'] = '/tmp'

# Tipos de archivos permitidos para subir
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ruta para acceder fácilmente al folder en otras partes del código
ruta_comprobantes = app.config['UPLOAD_FOLDER']

# Función para validar extensión permitida
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------- Vistas --------------------------
@app.route('/loguear', methods=['GET', 'POST'])
def loguear():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasenia = request.form['contrasenia']

        db = get_db_connection()
        user = ModuleUser.get_by_username(db, nombre_usuario)

        if not user:
            flash('Error en el campo usuario: el usuario no existe', 'danger')
        elif not User.check_password(user.contrasenia, contrasenia):
            flash('Error en el campo contraseña: contraseña incorrecta', 'danger')
        else:
            login_user(user)
            return redirect(url_for('index'))

        return redirect(url_for('loguear'))

    return render_template('iniciarSesion/sesion.html')

def grabaciones_cursos():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('''
                SELECT id_sesion, fecha_curso, categoria
                FROM detalles_sesiones;
                ''')
    sesiones = cur.fetchall()

    hoy = date.today()
    ids_para_actualizar =[
        s[0] for s in sesiones
        if s[2] == 2 and s[1] < hoy
    ]

    if ids_para_actualizar:
        cur.execute('''
            UPDATE sesiones_curso
            SET categoria = 3
            WHERE id_sesion = ANY(%s);
        ''', (ids_para_actualizar,))
        
    con.commit()
    cur.close()
    con.close()
    
def pasadas_especializaciones():
    con = get_db_connection()
    cur = con.cursor()

    cur.execute('''
                    SELECT id_sesion, fecha_curso, categoria
                    FROM public.detalles_sesiones;
                ''')
    sesiones = cur.fetchall()

    hoy = date.today()

    # Filtrar solo los que tienen categoria 1 y fecha pasada
    ids_para_actualizar = [
        s[0] for s in sesiones
        if s[2] == 1 and s[1] < hoy
    ]

    if ids_para_actualizar:
        cur.execute('''
                        UPDATE public.sesiones_curso
                        SET categoria = 6
                        WHERE id_sesion = ANY(%s);
                    ''', (ids_para_actualizar,))

    con.commit()
    cur.close()
    con.close()

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('loguear'))

@app.route("/")
def login():
    return render_template('/iniciarSesion/sesion.html')

@app.route("/index")
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cursos")
    total_cursos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM participantes")
    total_participantes = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) 
        FROM asistencias_detalladas_constancias 
        WHERE constancia_enviada = False AND (validacion_pago = %s OR validacion_pago = %s)
    ''', (1, 2))
    constancias_pendientes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ponentes")
    total_ponentes = cursor.fetchone()[0]

    conn.close()

    return render_template("/index.html",
        total_cursos=total_cursos,
        total_participantes=total_participantes,
        constancias_pendientes=constancias_pendientes,
        total_ponentes=total_ponentes
    )
    
@app.route("/actualizar_grabaciones")
@login_required
def actualizar_grabaciones():
    grabaciones_cursos()
    flash("En vivos pasados actualizados correctamente.", "success")
    return redirect(url_for('index'))

@app.route("/actualizar_especializaciones")
@login_required
def actualizar_especializaciones():
    pasadas_especializaciones()
    flash("Especializaciones pasadas actualizadas correctamente.", "success")
    return redirect(url_for("index"))

@app.errorhandler(401)
def unauthorized_error(error):
    return render_template('401.html'), 401
# -------------------------- Desarrollo local --------------------------
if __name__ == '__main__':
    csrf.init_app(app)
    app.register_error_handler(404, lambda error: render_template('404.html'))
    app.register_error_handler(401, lambda error: redirect(url_for('401.html')))
    app.run(debug=True, port=5000)
