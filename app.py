from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import login_required, login_user, logout_user, LoginManager, current_user
import csv
import pymysql
from config import db
from models.usuario import User
from models.tarea import Tarea
from models.curso import Curso
import pymysql.cursors


app = Flask(__name__)
app.secret_key = 'navas'  # Cambiar por una clave segura

login_manager = LoginManager()
login_manager.init_app(app)  # vincula Flask-Login app
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."


# ------------LOGIN------------
@app.route('/', methods=['GET', 'POST'])
def login():
    mensaje = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            # Buscar el usuario en la base de datos
            user = User.get_by_username(username)  # Usar el método estático de la clase User
            
            if user and user.password == password:  # Comparar contraseñas
                login_user(user)  
                
                if user.role == 'Profesor':
                    return redirect(url_for('vista_profesor'))
                elif user.role == 'Alumno':
                    return redirect(url_for('vista_alumno'))
            else:
                mensaje = "Datos incorrectos"
        
        except Exception as e:
            print("Error e" + e)
    
    return render_template('login.html', mensaje = mensaje)

# ------------REGISTRO------------
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    mensaje = ""  # Variable para el mensaje
    cursor = db.cursor()
    
    # Obtener todos los cursos
    cursor.execute("SELECT nombre FROM cursos")  
    cursos = [curso[0] for curso in cursor.fetchall()]  

    if request.method == 'POST':
        dni = request.form['dni']  
        username = request.form['username']
        password = request.form['password']
        curso = request.form['curso']
        role = request.form['select_role']

        # Verificar si el DNI ya existe
        cursor.execute("SELECT dni FROM usuarios WHERE dni = %s", (dni,))
        if cursor.fetchone():
            mensaje = "Error: El DNI ya está registrado."
        else:
            try:
                sql = "INSERT INTO usuarios (dni, username, contraseña, curso, role) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (dni, username, password, curso, role))
                db.commit()
                mensaje = f"Usuario '{username}' creado correctamente."
            except Exception as e:
                db.rollback()
                mensaje = f"Error al registrar el usuario: {str(e)}"

    return render_template('registration.html', cursos=cursos, mensaje=mensaje)


# ------------VISTA DE ALUMNO ------------
@app.route('/vista_alumno')
@login_required
def vista_alumno():
    cursor = db.cursor()
    # current_user.username para obtener el usuario actual
    sql = "SELECT username FROM usuarios WHERE username = %s"
    cursor.execute(sql, (current_user.username,))
    usuario = cursor.fetchone()
    nombre_usuario = usuario[0] if usuario else "Alumno"
    
    sql_tareas = "SELECT id, nombre_tarea, nombre_alumno, descripcion, fecha_entrega, estado FROM tareas WHERE nombre_alumno = %s"
    sql_asistencias = "SELECT id, nombre_alumno, nombre, descripcion, fecha FROM asistencias WHERE nombre_alumno = %s"

    cursor.execute(sql_tareas, (nombre_usuario,))
    tareas = cursor.fetchall()
    cursor.execute(sql_asistencias, (nombre_usuario,))
    asistencias = cursor.fetchall()

    # Preparar los datos para el gráfico (etiquetas y valores)
    labels = ['Entregadas', 'Pendientes'] 
    values = [0, 0]  
    for tarea in tareas:
        estado = tarea[5]  
        if estado == 1:  
            values[0] += 1
        else:
            values[1] += 1

    # Pasar los datos a la plantilla
    chart_data = {'labels': labels, 'values': values}
    print(chart_data)
    
    return render_template('alumno_dashboard.html', nombre_usuario=nombre_usuario, tareas=tareas, asistencias=asistencias, chart_data=chart_data)


# ------------ ENTREGAR TAREA ------------
@app.route('/entregar_tarea/<int:tarea_id>', methods=['POST'])
@login_required
def entregar_tarea(tarea_id):
    cursor = db.cursor()
    sql = "UPDATE tareas SET estado = 1 WHERE id = %s"
    cursor.execute(sql, (tarea_id,))
    db.commit()
    return redirect(url_for('vista_alumno'))




# ------------VISTA DE PROFESOR ------------

@app.route('/vista_profesor')
@login_required
def vista_profesor():
    cursor = db.cursor()
    sql = "SELECT username FROM usuarios WHERE username = %s"
    cursor.execute(sql, (current_user.username,))
    usuario = cursor.fetchone()
    nombre_usuario = usuario[0] if usuario else "Profesor"
    
    return render_template('profesor_dashboard.html', nombre_usuario=nombre_usuario)

# ---------LOAD USER ------------

@login_manager.user_loader
def load_user(user_id):
    """Carga un usuario por su ID desde la base de datos."""
    cursor = db.cursor()
    sql = "SELECT id_usuario, username, contraseña, curso, role FROM usuarios WHERE id_usuario = %s"
    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()

    if result:
        id, username, password, course, role = result
        return User(id, username, password, course, role)
    return None

# ------------LOGOUT------------
@app.route('/logout')
def logout():
    logout_user()  # funcion de Flask-Login para cerrar sesión
    return redirect(url_for('login'))



# ------------CREAR CURSO------------
@app.route('/crear_curso', methods=['GET', 'POST'])
def crear_curso():
    mensaje = None  # Para mostrar el mensaje en la vista

    if request.method == 'POST':
        nombre_curso = request.form['nombre_curso']
        profesor = request.form['profesor']

        cursor = db.cursor()
        cursor.execute("SELECT * FROM cursos WHERE nombre = %s", (nombre_curso,))
        curso_existente = cursor.fetchone()

        if curso_existente:
            mensaje = f"El curso '{nombre_curso}' ya existe. Introduce un nombre diferente."
        else:
            try:
                cursor.execute("INSERT INTO cursos (nombre, profesor) VALUES (%s, %s)", (nombre_curso, profesor))
                db.commit()
                mensaje = f"El curso '{nombre_curso}' se ha creado correctamente."
            except Exception as e:
                db.rollback()
                mensaje = f"Error al crear el curso: {str(e)}"

    return render_template('crear_curso_vista.html', mensaje=mensaje)




# ------------CREAR TAREA------------
@app.route('/crear_tarea', methods=['GET', 'POST'])
def crear_tarea():
    mensaje = None  # Para mostrar el mensaje en la vista
    cursor = db.cursor()
    if request.method == 'POST':
        alumno = request.form['alumno']
        nombre_tarea = request.form['nombre_tarea']
        descripcion_tarea = request.form['descripcion_tarea']
        fecha_entrega = request.form['fecha_entrega']

        

        # Verificar si la tarea ya existe
        cursor.execute("SELECT * FROM tareas WHERE nombre_tarea = %s AND nombre_alumno = %s", (nombre_tarea, alumno))
        tarea_existente = cursor.fetchone()

        if tarea_existente:
            mensaje = f"La tarea '{nombre_tarea}' para el alumno '{alumno}' ya existe."
        else:
            try:
                # Insertar la nueva tarea en la base de datos
                cursor.execute("""
                    INSERT INTO tareas (nombre_tarea, nombre_alumno, fecha_entrega, descripcion)
                    VALUES (%s, %s, %s, %s)
                """, (nombre_tarea, alumno, fecha_entrega, descripcion_tarea))
                db.commit()
                mensaje = f"La tarea '{nombre_tarea}' se ha creado correctamente."
            except Exception as e:
                db.rollback()
                mensaje = f"Error al crear la tarea: {str(e)}"

    # Obtener los alumnos para mostrarlos en el formulario
    cursor.execute("SELECT username FROM usuarios WHERE role = 'Alumno'")
    alumnos = cursor.fetchall()

    return render_template('crear_tarea_vista.html', alumnos=alumnos, mensaje=mensaje)


# ------------CREAR ASISTENCIA------------
@app.route('/crear_asistencia', methods=['GET', 'POST'])
@login_required
def crear_asistencia():
    mensaje = None  # Para mostrar el mensaje en la vista
    cursor = db.cursor()  # Inicializar el cursor antes del if

    if request.method == 'POST':
        nombre_alumno = request.form['alumno']
        nombre_asistencia = request.form['nombre_asistencia']
        descripcion = request.form['descripcion_asistencia']
        fecha = request.form['fecha_falta']

        # Verificar si la asistencia ya existe
        cursor.execute("SELECT * FROM asistencias WHERE nombre = %s AND nombre_alumno = %s AND fecha = %s",
                       (nombre_asistencia, nombre_alumno, fecha))
        asistencia_existente = cursor.fetchone()

        if asistencia_existente:
            mensaje = f"La asistencia '{nombre_asistencia}' para '{nombre_alumno}' ya existe en la fecha {fecha}."
        else:
            try:
                # Insertar la asistencia en la base de datos
                cursor.execute("""
                    INSERT INTO asistencias (nombre_alumno, nombre, descripcion, fecha)
                    VALUES (%s, %s, %s, %s)
                """, (nombre_alumno, nombre_asistencia, descripcion, fecha))
                db.commit()
                mensaje = f"Asistencia '{nombre_asistencia}' creada correctamente."
            except Exception as e:
                db.rollback()
                mensaje = f"Error al crear la asistencia: {str(e)}"

    # Obtener los alumnos para mostrarlos en el formulario
    cursor.execute("SELECT username FROM usuarios WHERE role = 'Alumno'")
    alumnos = cursor.fetchall()

    cursor.close()  # Cerrar el cursor después de usarlo

    return render_template('crear_asistencia_vista.html', alumnos=alumnos, mensaje=mensaje)




# ------------EDITAR CURSO------------
@app.route('/editar_cursos')
def editar_cursos():
    cursor = db.cursor(pymysql.cursors.DictCursor)  # para pasar los datos de bdd a aqui
    cursor.execute("SELECT * FROM cursos")
    cursos = cursor.fetchall()
    return render_template('editar_cursos_vista.html', cursos=cursos)

# ------------ELIMINAR CURSO------------
@app.route('/eliminar_curso/<int:id>')
def eliminar_curso(id):
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM cursos WHERE id = %s", (id,))
        db.commit()
    except Exception as e:
        db.rollback()
    
    return redirect(url_for('editar_cursos'))








if __name__ == '__main__':
    app.run(debug=True)
