from flask import Flask, current_app, render_template, url_for, redirect, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect

from app.models.ModelUser import ModuleUser
from app.models.entities.user import User
from app.routes.utils.utils import get_db_connection

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

# -------------------------- Inicialización --------------------------
app = Flask(__name__)
csrf = CSRFProtect(app)
app.secret_key = 'secret'

# Login
login_manager = LoginManager(app)

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

# Configuración
app.config['UPLOAD_FOLDER'] = './static/img/uploads/'
ruta_comprobantes = app.config['UPLOAD_FOLDER']
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# -------------------------- Vistas --------------------------
@app.route('/loguear', methods=['GET', 'POST'])
def loguear():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasenia = request.form['contrasenia']
        user_input = User(0, nombre_usuario, contrasenia)
        loged_user = ModuleUser.login(get_db_connection(), user_input)

        if loged_user:
            login_user(loged_user)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

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

    cursor.execute("SELECT COUNT(*) FROM asistencias_detalladas_constancias WHERE constancia_enviada = False")
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

# -------------------------- Desarrollo local --------------------------
if __name__ == '__main__':
    csrf.init_app(app)
    app.register_error_handler(404, lambda error: render_template('404.html'), 404)
    app.register_error_handler(401, lambda error: redirect(url_for('login')))
    app.run(debug=True, port=5000)
