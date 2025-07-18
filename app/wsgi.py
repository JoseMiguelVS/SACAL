from flask import redirect, render_template, url_for
from app import app
from flask_wtf.csrf import CSRFProtect

# Inicializa CSRF
csrf = CSRFProtect(app)

# Registra manejadores personalizados de errores
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('404.html'), 404

@app.errorhandler(401)
def acceso_no_autorizado(error):
    return redirect(url_for('login'))
