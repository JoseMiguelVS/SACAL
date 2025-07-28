from .entities.user import User

class ModuleUser:
    @classmethod
    def login(cls, db, user_input):
        try:
            cur = db.cursor()
            sql = "SELECT id_empleado, nombre_usuario, contrasenia_empleado, estado, rol FROM empleados WHERE estado='True' AND nombre_usuario=%s"
            cur.execute(sql, (user_input.nombre_usuario,))
            row = cur.fetchone()
            
            if row:
                if User.check_password(row[2], user_input.contrasenia):
                    user = User(
                        id_empleado=row[0],
                        nombre_usuario=row[1],
                        contrasenia=None,
                        estado=row[3],
                        rol=row[4]
                    )
                    return user
            return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(cls, db, id_empleado):
        try:
            cur = db.cursor()
            sql = "SELECT id_empleado, nombre_usuario, contrasenia_empleado, rol FROM empleados WHERE estado='True' AND id_empleado=%s"
            cur.execute(sql, (id_empleado,))
            row = cur.fetchone()
            if row:
                return User(
                    id_empleado=row[0],
                    nombre_usuario=row[1],
                    contrasenia=None,
                    estado=None,
                    rol=row[3]
                )
            return None
        except Exception as ex:
            raise Exception(ex)
        
    @classmethod
    def get_by_username(cls, db, nombre_usuario):
        try:
            cur = db.cursor()
            sql = "SELECT id_empleado, nombre_usuario, contrasenia_empleado, estado, rol FROM empleados WHERE estado='True' AND nombre_usuario=%s"
            cur.execute(sql, (nombre_usuario,))
            row = cur.fetchone()
            if row:
                return User(
                    id_empleado=row[0],
                    nombre_usuario=row[1],
                    contrasenia=row[2],  # Conservamos la contraseña para validarla después
                    estado=row[3],
                    rol=row[4]
                )
            return None
        except Exception as ex:
            raise Exception(ex)

