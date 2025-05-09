from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

class User(UserMixin):

    def get_id(self):
        return(self.id_empleado)
    
    def __init__(self,id_empleado,nombre_usuario,contrasenia,estado) -> None:
        self.id_empleado=id_empleado  #0
        self.nombre_usuario=nombre_usuario #1
        self.contrasenia=contrasenia #2
        self.estado=estado #3
       
    @classmethod
    def check_password(self, hashed_password, contrasenia):
        return check_password_hash(hashed_password, contrasenia)
    
# print(generate_password_hash("1234"))