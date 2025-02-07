from config import db

class Curso:
    def __init__(self, nombre, profesor, alumnos=None):
        self.nombre = nombre       # Nombre del curso
        self.profesor = profesor   # Profesor asignado al curso
        self.alumnos = alumnos if alumnos is not None else []  # Lista de alumnos (por defecto vacía)

    def get_nombre(self):
        return self.nombre

    @staticmethod
    def get_by_nombre(nombre):
        """Busca un curso en la base de datos por su nombre."""
        cursor = db.cursor()
        sql = "SELECT nombre, profesor FROM cursos WHERE nombre = %s"
        cursor.execute(sql, (nombre,))
        result = cursor.fetchone()

        if result:
            nombre, profesor = result
            # Obtener los alumnos asignados a este curso
            sql_alumnos = "SELECT a.username FROM alumnos a INNER JOIN cursos_alumnos ca ON a.id_usuario = ca.id_alumno INNER JOIN cursos c ON c.id_curso = ca.id_curso WHERE c.nombre = %s"
            cursor.execute(sql_alumnos, (nombre,))
            alumnos = [alumno[0] for alumno in cursor.fetchall()]
            return Curso(nombre, profesor, alumnos)
        return None

    @staticmethod
    def get_all_cursos():
        """Devuelve todos los cursos disponibles con sus alumnos."""
        cursor = db.cursor()
        sql = "SELECT nombre, profesor FROM cursos"
        cursor.execute(sql)
        results = cursor.fetchall()

        cursos = []
        for result in results:
            nombre, profesor = result
            # Obtener los alumnos asignados a este curso
            sql_alumnos = "SELECT a.username FROM alumnos a INNER JOIN cursos_alumnos ca ON a.id_usuario = ca.id_alumno INNER JOIN cursos c ON c.id_curso = ca.id_curso WHERE c.nombre = %s"
            cursor.execute(sql_alumnos, (nombre,))
            alumnos = [alumno[0] for alumno in cursor.fetchall()]
            cursos.append(Curso(nombre, profesor, alumnos))
        return cursos
