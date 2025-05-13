from flask import Flask, render_template, url_for, redirect, request, flash
from flask_login import LoginManager

from routes.empleados.routes import empleados
from routes.ponentes.routes import ponentes
from routes.categorias.routes import categorias
from routes.paquetes.routes import paquetes

from flask import Flask, render_template, url_for, redirect, request, flash
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required

from models.ModelUser import ModuleUser
from models.entities.user import User
from routes.utils.utils import get_db_connection

app = Flask(__name__)
csrf = CSRFProtect(app) 
app.secret_key = 'secret'

#--------------------------------Login------------------------------------------
Login_manager_app=LoginManager(app)
@Login_manager_app.user_loader
def load_user(idusuarios):
    return ModuleUser.get_by_id(get_db_connection(),idusuarios)

#--------------------------------------------------------inicio de sesion --------------------------------------------
@app.route('/loguear', methods=('GET','POST'))
def loguear():
    if request.method == 'POST':
        nombre_usuario=request.form['nombre_usuario']
        contrasenia_empleado=request.form['contrasenia']
        user=User(0,nombre_usuario,contrasenia_empleado,None)
        loged_user=ModuleUser.login(get_db_connection(),user)

        if loged_user!= None:
            if loged_user.contrasenia:
                login_user(loged_user)
                return redirect(url_for('index'))
            else:
                flash('Nombre de usuario y/o contraseña incorrecta.')
                return redirect(url_for('login'))
        else:
            flash('Nombre de usuario y/o contraseña incorrecta.')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Registro de Blueprints
app.register_blueprint(empleados)
app.register_blueprint(ponentes)
app.register_blueprint(categorias)
app.register_blueprint(paquetes)

# Rutas principales
@app.route("/")
def login():
    return render_template('/iniciarSesion/sesion.html')

@app.route("/index")
@login_required
def index():
    return render_template('/index.html')

if __name__ == "__main__":
    app.run(debug=True)
