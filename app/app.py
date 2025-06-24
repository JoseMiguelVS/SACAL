from flask import Flask, current_app, render_template, url_for, redirect, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect

from models.ModelUser import ModuleUser
from models.entities.user import User
from routes.utils.utils import get_db_connection

# Importa tus Blueprints
from routes.empleados.routes import empleados
from routes.ponentes.routes import ponentes
from routes.categorias.routes import categorias
from routes.paquetes.routes import paquetes
from routes.cursos.routes import cursos
from routes.participantes.routes import participantes
from routes.sesiones.routes import sesiones
from routes.constancias.routes import constancias
from routes.temas.routes import temas
from routes.pagos.routes import pagos

# ...
app = Flask(__name__)
csrf = CSRFProtect(app) 
app.secret_key = 'secret'

# Login
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(idusuarios):
    return ModuleUser.get_by_id(get_db_connection(), idusuarios)

# Registro de Blueprints
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

#-------------------------- Login y Rutas --------------------------
@app.route('/loguear', methods=('GET', 'POST'))
def loguear():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasenia_empleado = request.form['contrasenia']
        user = User(0, nombre_usuario, contrasenia_empleado, None)
        loged_user = ModuleUser.login(get_db_connection(), user)

        if loged_user and loged_user.contrasenia:
            login_user(loged_user)
            return redirect(url_for('index'))
        else:
            flash('Nombre de usuario y/o contraseña incorrecta.')
            return redirect(url_for('login'))
    return redirect(url_for('login'))

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
    return render_template('/index.html')

app.config['UPLOAD_FOLDER'] = './static/img/uploads/'
ruta_comprobantes = app.config['UPLOAD_FOLDER']
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

#-------------------------- Errores --------------------------
def pagina_no_encontrada(error):
    return render_template('404.html'), 404

def acceso_no_autorizado(error):
    return redirect(url_for('login'))

#-------------------------- Iniciar servidor --------------------------
if __name__ == '__main__':
    csrf.init_app(app)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, acceso_no_autorizado)
    app.run(debug=True, port=5000)
