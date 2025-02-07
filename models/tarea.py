from config import db

class Tarea:
    def __init__(self, id, nombre_tarea, nombre_alumno, fecha_entrega):
        self.id = id
        self.nombre_tarea = nombre_tarea
        self.nombre_alumno = nombre_alumno
        self.fecha_entrega = fecha_entrega

    @staticmethod
    def create_task(nombre_tarea, nombre_alumno, fecha_entrega):
        """Crea una nueva tarea en la base de datos."""
        cursor = db.cursor()
        sql = "INSERT INTO tareas (nombre_tarea, nombre_alumno, fecha_entrega) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nombre_tarea, nombre_alumno, fecha_entrega))
        db.commit()
        return cursor.lastrowid  # Devuelve el ID de la tarea creada

    @staticmethod
    def get_tasks_by_student(nombre_alumno):
        """Obtiene todas las tareas asignadas a un alumno."""
        cursor = db.cursor()
        sql = "SELECT id, nombre_tarea, nombre_alumno, fecha_entrega FROM tareas WHERE nombre_alumno = %s"
        cursor.execute(sql, (nombre_alumno,))
        tareas = cursor.fetchall()
        return [Tarea(*t) for t in tareas]  # Retorna una lista de objetos Tarea
