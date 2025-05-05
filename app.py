from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
# Carga de variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from io import BytesIO
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from flask_login import login_required, current_user
from functools import wraps

# Importar db de forma tardía para evitar importación circular
from models import db, RegistroHoras, ClienteModel

# Función para convertir una hora en formato de texto a un número decimal
def convertir_hora_a_decimal(hora_str):
    try:
        return float(int(hora_str.strip()))
    except ValueError:
        return 0.0

# Decorador para asegurarse de que solo el superadministrador pueda acceder
def superadmin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.role != 'superadmin':  # Verifica el rol del usuario
            flash('No tienes permisos para realizar esta acción', 'danger')
            return redirect(url_for('index'))  # Redirige a la página principal
        return f(*args, **kwargs)
    return wrapper

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos con PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'clave_secreta_para_sesiones'

# Habilita la recarga automática de plantillas y la caché de Jinja
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.cache = {}

# Inicializa la base de datos y el sistema de migración
db.init_app(app)  # Se inicializa db antes de usarlo
migrate = Migrate(app, db)

# Asegúrate de que la base de datos se cree si no existe
with app.app_context():
    db.create_all()

# ─── Modelos ─────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    registros = db.relationship('Registro', backref='user', lazy=True)

class Registro(db.Model):
    __tablename__ = 'registros'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fecha = db.Column(db.String(50), nullable=False)
    entrada = db.Column(db.String(50), nullable=False)
    salida = db.Column(db.String(50), nullable=False)
    almuerzo = db.Column(db.Float, default=0.0)
    viaje_ida = db.Column(db.Float, default=0.0)
    viaje_vuelta = db.Column(db.Float, default=0.0)
    km_ida = db.Column(db.Float, default=0.0)
    km_vuelta = db.Column(db.Float, default=0.0)
    horas = db.Column(db.Float, nullable=False)  # Asegúrate de que este campo no sea nulo
    tarea = db.Column(db.Text, default="")
    cliente = db.Column(db.Text, default="")
    comentarios = db.Column(db.Text, default="")


# ─── Inicialización de la base de datos ─────────
with app.app_context():
    db.create_all()
    if not User.query.filter(db.func.lower(User.username) == 'guillermo gutierrez').first():
        superadmin = User(username='guillermo gutierrez', password='0000', role='superadmin')
        db.session.add(superadmin)
        db.session.commit()

# ─── Rutas ──────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def inicio():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password']

        user = User.query.filter(
            db.func.lower(User.username) == username,
            User.password == password
        ).first()

        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', category='danger')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        fecha = request.form['fecha']
        entrada = request.form['entrada']
        salida = request.form['salida']

        # Verificar que los campos de entrada y salida no estén vacíos
        if not entrada or not salida:
            flash("Por favor, complete las horas de entrada y salida.", "danger")
            return redirect(url_for('dashboard'))

        try:
            almuerzo_horas = int(request.form.get('almuerzo_horas', 0))
            almuerzo_minutos = int(request.form.get('almuerzo_minutos', 0))
        except ValueError:
            flash("El tiempo de almuerzo debe ser un número válido", "danger")
            return redirect(url_for('dashboard'))

        almuerzo = timedelta(hours=almuerzo_horas, minutes=almuerzo_minutos)

        try:
            viaje_ida = float(request.form.get('viaje_ida', 0) or 0)
            viaje_vuelta = float(request.form.get('viaje_vuelta', 0) or 0)
            km_ida = float(request.form.get('km_ida', 0) or 0)
            km_vuelta = float(request.form.get('km_vuelta', 0) or 0)
        except ValueError:
            flash("Las horas de viaje y kilómetros deben ser números válidos.", "danger")
            return redirect(url_for('dashboard'))

        tarea = request.form.get('tarea', '').strip()
        cliente = request.form.get('cliente', '').strip()
        comentarios = request.form.get('comentarios', '').strip()

        try:
            formato_hora = "%H:%M"
            t_entrada = datetime.strptime(entrada, formato_hora)
            t_salida = datetime.strptime(salida, formato_hora)

            if t_salida < t_entrada:
                t_salida += timedelta(days=1)

            tiempo_total = t_salida - t_entrada - almuerzo
            horas_trabajadas = tiempo_total.total_seconds() / 3600
        except ValueError:
            flash("Formato de hora incorrecto. Use HH:MM.", "danger")
            return redirect(url_for('dashboard'))

        # Crear nuevo registro en la base de datos
        nuevo_registro = Registro(
            user_id=session['user_id'],
            fecha=fecha,
            entrada=t_entrada.strftime("%H:%M"),  # Convierte la hora de entrada a cadena
            salida=t_salida.strftime("%H:%M"),    # Convierte la hora de salida a cadena
            almuerzo=round(almuerzo.total_seconds() / 3600, 2),
            horas=round(horas_trabajadas, 2),
            viaje_ida=viaje_ida,
            viaje_vuelta=viaje_vuelta,
            km_ida=km_ida,
            km_vuelta=km_vuelta,
            tarea=tarea,
            cliente=cliente,
            comentarios=comentarios
        )

        db.session.add(nuevo_registro)
        db.session.commit()
        flash('Registro guardado exitosamente', category='success')
        return redirect(url_for('dashboard'))

    # GET - mostrar los registros y total de horas
    filtros = request.args
    registros_query = Registro.query.filter_by(user_id=session['user_id'])

    if 'fecha' in filtros:
        registros_query = registros_query.filter_by(fecha=filtros['fecha'])

    registros = registros_query.order_by(Registro.fecha.desc()).all()

    total_horas = sum([
        (r.horas or 0) + (r.viaje_ida or 0) + (r.viaje_vuelta or 0)
        for r in registros
    ])
    total_km = sum([
        (r.km_ida or 0) + (r.km_vuelta or 0)
        for r in registros
    ])

    return render_template(
        'dashboard.html',
        username=session['username'],
        role=session['role'],
        registros=registros,
        total_horas=round(total_horas, 2),
        total_km=round(total_km, 2)
    )


@app.route('/exportar_excel')
def exportar_excel():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    query = Registro.query

    # Si no es admin o superadmin, se filtra por el usuario actual
    if role not in ['admin', 'superadmin']:
        query = query.filter_by(user_id=session['user_id'])

    # Si hay filtros de fechas, se aplican
    if fecha_desde and fecha_hasta:
        query = query.filter(Registro.fecha.between(fecha_desde, fecha_hasta))

    registros = query.all()

    # Armar el DataFrame para exportar
    df = pd.DataFrame([{
        'usuario': r.user.username,
        'fecha': r.fecha,
        'entrada': r.entrada,
        'salida': r.salida,
        'almuerzo': r.almuerzo,
        'viaje_ida': r.viaje_ida,
        'viaje_vuelta': r.viaje_vuelta,
        'horas_laborales': r.horas,
        'horas_totales': round((r.horas or 0) + (r.viaje_ida or 0) + (r.viaje_vuelta or 0), 2),
        'km_ida': r.km_ida,
        'km_vuelta': r.km_vuelta,
        'km_totales': (r.km_ida or 0) + (r.km_vuelta or 0),
        'tarea': r.tarea,
        'cliente': r.cliente,
        'comentarios': r.comentarios
    } for r in registros])

    # Crear archivo en memoria
    archivo = BytesIO()
    with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Registros')
        ws = writer.sheets['Registros']
        
        from openpyxl.styles import Font, PatternFill, Border, Side

        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        zebra_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

        # Aplicar estilos a los encabezados
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border

        # Aplicar estilos al resto de las filas
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.border = thin_border
            if row[0].row % 2 == 0:  # zebra stripe
                for cell in row:
                    cell.fill = zebra_fill

        # Aplicar filtros y ajustar anchos
        ws.auto_filter.ref = ws.dimensions
        for col_num, column_cells in enumerate(ws.columns, 1):
            max_length = max((len(str(cell.value)) for cell in column_cells if cell.value), default=0)
            ws.column_dimensions[get_column_letter(col_num)].width = max_length + 2

    archivo.seek(0)

    return send_file(
        archivo,
        as_attachment=True,
        download_name=f"registros_{session['username']}.xlsx"
    )





@app.route('/editar_registro/<int:id>', methods=['GET', 'POST'])
def editar_registro(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    registro = Registro.query.get_or_404(id)

    if request.method == 'POST':
        fecha = request.form['fecha']
        entrada = request.form['entrada']
        salida = request.form['salida']

        almuerzo_horas = int(request.form.get('almuerzo_horas', 0))       
        almuerzo = almuerzo_horas

        try:
            registro.viaje_ida = int(request.form['viaje_ida'])
            registro.viaje_vuelta = int(request.form['viaje_vuelta'])
            registro.km_ida = int(request.form['km_ida'])
            registro.km_vuelta = int(request.form['km_vuelta'])

            # Validación dentro del try
            if registro.viaje_ida < 0 or registro.viaje_vuelta < 0:
                flash("Las horas de viaje no pueden ser negativas", "danger")
                return redirect(url_for('editar_registro', id=id))

        except ValueError:
            flash("Por favor, ingresá valores válidos en los campos numéricos", "danger")
            return redirect(url_for('editar_registro', id=id))

        tarea = request.form.get('tarea', '')
        cliente = request.form.get('cliente', '')
        comentarios = request.form.get('comentarios', '')

        try:
            t_entrada = datetime.strptime(entrada, "%H:%M")
            t_salida = datetime.strptime(salida, "%H:%M")
            horas_trabajadas = (t_salida - t_entrada - timedelta(hours=almuerzo)).total_seconds() / 3600
        except ValueError:
            flash("Error en el formato de hora. Use HH:MM", "danger")
            return redirect(url_for('editar_registro', id=id))

        # Guardar cambios
        registro.fecha = fecha
        registro.entrada = entrada
        registro.salida = salida
        registro.almuerzo = round(almuerzo, 2)
        registro.horas = round(horas_trabajadas, 2)
        registro.viaje_ida = registro.viaje_ida
        registro.viaje_vuelta = registro.viaje_vuelta
        registro.km_ida = registro.km_ida
        registro.km_vuelta = registro.km_vuelta
        registro.tarea = tarea
        registro.cliente = cliente
        registro.comentarios = comentarios

        db.session.commit()
        flash('Registro actualizado exitosamente', category='success')

        # Redirigir según rol
        return redirect(url_for('admin') if session['role'] in ['admin', 'superadmin'] else url_for('dashboard'))

    return render_template('editar_registro.html', registro=registro)





@app.route('/borrar_registro/<int:id>', methods=['POST'])
def borrar_registro(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    registro = Registro.query.get_or_404(id)
    db.session.delete(registro)
    db.session.commit()
    return redirect(url_for('admin') if session['role'] == 'superadmin' else url_for('dashboard'))

@app.route('/crear_admin', methods=['GET', 'POST'])
def crear_admin():
    if 'user_id' not in session or session['role'] != 'superadmin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password')
        confirmar = request.form.get('confirmar_password')

        if not username or not password or not confirmar:
            flash('Todos los campos son obligatorios.', category='warning')
            return render_template('crear_admin.html')

        if password != confirmar:
            flash('Las contraseñas no coinciden.', category='danger')
            return render_template('crear_admin.html')

        if User.query.filter_by(username=username).first():
            flash('Ese nombre de usuario ya existe.', category='danger')
        else:
            nuevo_admin = User(username=username, password=password, role='admin')
            db.session.add(nuevo_admin)
            db.session.commit()
            flash('Administrador creado correctamente', category='success')

    return render_template('crear_admin.html')


@app.route('/administrator', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session or session['role'] not in ['admin', 'superadmin']:
        return redirect(url_for('login'))

    filtro_usuario = request.form.get('filtro_usuario') if request.method == 'POST' else None

    usuarios = User.query.with_entities(User.id, User.username).all()

    if filtro_usuario:
        registros = db.session.query(Registro, User).join(User).filter(User.id == filtro_usuario).order_by(Registro.fecha.desc()).all()
    else:
        registros = db.session.query(Registro, User).join(User).order_by(Registro.fecha.desc()).all()

    return render_template('admin.html', registros=registros, usuarios=usuarios,
                           filtro_usuario=filtro_usuario,
                           username=session['username'], role=session['role'])


@app.route('/cambiar_password', methods=['GET', 'POST'])
def cambiar_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nueva = request.form['nueva']
        confirmar = request.form['confirmar']  # Se agrega para la comparación de contraseñas

        if nueva != confirmar:
            flash('Las contraseñas no coinciden.', category='danger')
            return render_template('cambiar_password.html')

        # Si las contraseñas coinciden, actualizarla en la base de datos
        user = User.query.get(session['user_id'])
        user.password = nueva
        db.session.commit()
        flash('Contraseña actualizada', category='success')

    return render_template('cambiar_password.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if 'user_id' not in session or session['role'] not in ['admin', 'superadmin']:
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password']
        confirmar = request.form['confirmar_password']

        if password != confirmar:
            flash('Las contraseñas no coinciden.', category='danger')
            return render_template('crear_usuario.html')

        if User.query.filter_by(username=username).first():
            flash('Ese nombre de usuario ya existe.', category='danger')
        else:
            nuevo_usuario = User(username=username, password=password, role='usuario')
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Usuario creado exitosamente.', category='success')


    return render_template('crear_usuario.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password']
        confirmar = request.form['confirmar_password']

        if password != confirmar:
            flash('Las contraseñas no coinciden.', category='danger')
            return render_template('registro.html')

        if User.query.filter_by(username=username).first():
            flash('Ese nombre de usuario ya existe.' , category='danger')
        else:
            nuevo_usuario = User(username=username, password=password, role='usuario')
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Usuario creado exitosamente. Ahora podés iniciar sesión.', category='success')
            return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/lista_usuarios')
def lista_usuarios():
    if 'user_id' not in session or session.get('role') != 'superadmin':
        return redirect(url_for('login'))

    usuarios = User.query.all()
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'user_id' not in session or session['role'] != 'superadmin':
        return redirect(url_for('login'))  # Si no es superadmin, redirigir al login

    user = User.query.get_or_404(id)  # Busca el usuario por ID, si no lo encuentra, lanza error 404

    if request.method == 'POST':  # Si se recibe una solicitud POST (cuando el formulario es enviado)
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']
        db.session.commit()  # Realiza el commit en la base de datos para guardar los cambios
        flash('Usuario actualizado correctamente', 'success')  # Mensaje de éxito
        return redirect(url_for('lista_usuarios'))  # Redirige a la lista de usuarios después de la edición

    return render_template('editar_usuarios.html', user=user)  # Si es GET, muestra el formulario con los datos actuales

@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    if 'user_id' not in session or session['role'] != 'superadmin':
        return redirect(url_for('login'))

    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado correctamente', 'danger')
    return redirect(url_for('lista_usuarios'))  # Cambio aquí
    
    
@app.route('/ver_cliente', methods=['GET', 'POST'])
def ver_cliente():
    clientes = Cliente.query.all()  # Obtener todos los clientes

    if request.method == 'POST':
        cliente_id = request.form['cliente']  # Obtener el ID del cliente seleccionado
        
        if not cliente_id:
            flash('Debe seleccionar un cliente.', 'danger')
            return redirect(url_for('ver_cliente'))
        
        cliente = Cliente.query.get(cliente_id)  # Obtener el cliente por su ID

        if cliente:
            return render_template('detalle_cliente.html', cliente=cliente)  # Muestra los detalles del cliente
        else:
            flash('Cliente no encontrado.', 'danger')
            return redirect(url_for('ver_cliente'))  # Redirige de vuelta si no se encuentra el cliente

    return render_template('ver_cliente.html', clientes=clientes)



@app.route('/agregar_cliente', methods=['GET', 'POST'])
@login_required
def agregar_cliente():
    # Solo el superadmin puede agregar clientes
    if current_user.role != 'superadmin':
        flash('Acceso denegado: solo el superadministrador puede agregar clientes.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form.get('telefono')

        # Validación de datos antes de guardarlos
        if not nombre or not direccion:
            flash('El nombre y la dirección son campos obligatorios.', 'danger')
            return redirect(url_for('agregar_cliente'))

        # Crear un nuevo cliente
        nuevo_cliente = Cliente(nombre=nombre, direccion=direccion, telefono=telefono)

        try:
            db.session.add(nuevo_cliente)
            db.session.commit()
            flash('Cliente agregado exitosamente.', 'success')
            return redirect(url_for('dashboard'))  # Redirige al dashboard superadmin
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar el cliente: {e}', 'danger')

    # Obtener todos los clientes para mostrarlos en el formulario
    clientes = Cliente.query.all()

    return render_template('agregar_cliente.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
