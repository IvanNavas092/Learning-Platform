from flask_login import UserMixin
from config import db

class User(UserMixin):
    def __init__(self, id, username, password, course, role):
        self.id = id                 # ID único del usuario
        self.username = username     # Nombre de usuario
        self.password = password     # Contraseña (idealmente cifrada)
        self.course = course         # Curso (puede ser None para profesores)
        self.role = role             # Rol (e.g., 'Alumno' o 'Profesor')

    def get_id(self):
        return str(self.id)

    @staticmethod
    def get_by_username(username):
        """Busca un usuario en la base de datos por su nombre de usuario."""
        cursor = db.cursor()
        sql = "SELECT id_usuario, username, contraseña, curso, role FROM usuarios WHERE username = %s"
        cursor.execute(sql, (username,))
        result = cursor.fetchone()

        if result:
            # Crear y devolver una instancia de User si el usuario existe
            id, username, password, course, role = result
            return User(id, username, password, course, role)
        return None
    

