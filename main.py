from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import qrcode
import io
import base64
from datetime import datetime, date
import os
from functools import wraps

# Configurar Flask con rutas absolutas
app = Flask(__name__)
app.secret_key = 'ayuntamiento_carmen_tequexquitla_2025'

# Configuración de la base de datos
DATABASE = 'database/asistencia.db'

# Configurar SQLite para Python 3.12
def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()

def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return datetime.fromisoformat(val.decode()).date()

def convert_timestamp(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.fromisoformat(val.decode())

# Registrar adaptadores para Python 3.12
sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("timestamp", convert_timestamp)

def init_db():
    """Inicializar la base de datos"""
    conn = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    
    # Crear tabla de administradores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            activo INTEGER DEFAULT 1
        )
    ''')
    
    # Crear tabla de empleados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            curp TEXT UNIQUE NOT NULL,
            puesto TEXT NOT NULL,
            departamento TEXT NOT NULL,
            codigo_qr TEXT UNIQUE NOT NULL,
            fecha_registro DATE DEFAULT CURRENT_DATE,
            activo INTEGER DEFAULT 1
        )
    ''')
    
    # Crear tabla de asistencias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER NOT NULL,
            fecha DATE NOT NULL,
            hora_entrada TIME,
            hora_salida TIME,
            observaciones TEXT,
            FOREIGN KEY (empleado_id) REFERENCES empleados (id)
        )
    ''')
    
    # Insertar administrador por defecto
    admin_password = generate_password_hash('admin2025')
    cursor.execute('''
        INSERT OR IGNORE INTO administradores (usuario, password, nombre)
        VALUES (?, ?, ?)
    ''', ('admin', admin_password, 'Administrador Sistema'))
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Obtener conexión a la base de datos con tipos de datos configurados"""
    return sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)

def login_required(f):
    """Decorador para requerir login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generar_codigo_qr(empleado_id, curp):
    """Generar código QR para empleado"""
    qr_data = f"EMP_{empleado_id}_{curp}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#932063", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    return qr_data, qr_base64

@app.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, password, nombre FROM administradores WHERE usuario = ? AND activo = 1', (usuario,))
        admin = cursor.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin[1], password):
            session['admin_id'] = admin[0]
            session['admin_nombre'] = admin[2]
            flash('Bienvenido al Sistema de Control de Asistencia', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Estadísticas del día
    hoy = date.today()
    cursor.execute('SELECT COUNT(*) FROM empleados WHERE activo = 1')
    total_empleados = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT empleado_id) FROM asistencias WHERE fecha = ?', (hoy,))
    asistencias_hoy = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM asistencias 
        WHERE fecha = ? AND hora_entrada IS NOT NULL AND hora_salida IS NULL
    ''', (hoy,))
    empleados_presentes = cursor.fetchone()[0]
    
    # Últimas asistencias
    cursor.execute('''
        SELECT e.nombre, e.apellidos, a.hora_entrada, a.hora_salida, a.fecha
        FROM asistencias a
        JOIN empleados e ON a.empleado_id = e.id
        ORDER BY a.fecha DESC, a.hora_entrada DESC
        LIMIT 10
    ''')
    ultimas_asistencias = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_empleados=total_empleados,
                         asistencias_hoy=asistencias_hoy,
                         empleados_presentes=empleados_presentes,
                         ultimas_asistencias=ultimas_asistencias)

@app.route('/empleados')
@login_required
def lista_empleados():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, nombre, apellidos, curp, puesto, departamento, fecha_registro, activo
        FROM empleados ORDER BY nombre, apellidos
    ''')
    empleados = cursor.fetchall()
    conn.close()
    
    return render_template('registro_personal.html', empleados=empleados)

@app.route('/empleado/nuevo', methods=['POST'])
@login_required
def nuevo_empleado():
    nombre = request.form['nombre']
    apellidos = request.form['apellidos']
    curp = request.form['curp'].upper().strip()
    puesto = request.form['puesto']
    departamento = request.form['departamento']
    
    # Validar CURP básica (18 caracteres)
    if len(curp) != 18:
        flash('Error: El CURP debe tener exactamente 18 caracteres', 'error')
        return redirect(url_for('lista_empleados'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insertar empleado
        cursor.execute('''
            INSERT INTO empleados (nombre, apellidos, curp, puesto, departamento, codigo_qr)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nombre, apellidos, curp, puesto, departamento, ''))
        
        empleado_id = cursor.lastrowid
        
        # Generar código QR
        codigo_qr, _ = generar_codigo_qr(empleado_id, curp)
        
        # Actualizar con código QR
        cursor.execute('UPDATE empleados SET codigo_qr = ? WHERE id = ?', (codigo_qr, empleado_id))
        
        conn.commit()
        conn.close()
        
        flash(f'Empleado {nombre} {apellidos} registrado exitosamente', 'success')
    except sqlite3.IntegrityError:
        flash('Error: El CURP ya está registrado', 'error')
    except Exception as e:
        flash(f'Error al registrar empleado: {str(e)}', 'error')
    
    return redirect(url_for('lista_empleados'))

@app.route('/empleado/qr/<int:empleado_id>')
@login_required
def ver_qr_empleado(empleado_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, apellidos, curp, codigo_qr FROM empleados WHERE id = ?', (empleado_id,))
    empleado = cursor.fetchone()
    conn.close()
    
    if empleado:
        _, qr_base64 = generar_codigo_qr(empleado_id, empleado[2])
        return jsonify({
            'success': True,
            'nombre': f"{empleado[0]} {empleado[1]}",
            'qr_image': qr_base64
        })
    
    return jsonify({'success': False, 'message': 'Empleado no encontrado'})

@app.route('/empleado/qr/<int:empleado_id>/download')
@login_required
def descargar_qr_empleado(empleado_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, apellidos, curp FROM empleados WHERE id = ?', (empleado_id,))
    empleado = cursor.fetchone()
    conn.close()
    
    if empleado:
        from flask import send_file
        import tempfile
        
        # Generar QR
        qr_data, _ = generar_codigo_qr(empleado_id, empleado[2])
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#932063", back_color="white")
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        img.save(temp_file.name)
        temp_file.close()
        
        filename = f"QR_{empleado[0]}_{empleado[1]}.png".replace(' ', '_')
        
        return send_file(temp_file.name, as_attachment=True, download_name=filename, mimetype='image/png')
    
    return jsonify({'success': False, 'message': 'Empleado no encontrado'})

@app.route('/empleado/editar/<int:empleado_id>', methods=['GET', 'POST'])
@login_required
def editar_empleado(empleado_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        puesto = request.form['puesto']
        departamento = request.form['departamento']
        activo = 1 if request.form.get('activo') == 'on' else 0
        
        try:
            cursor.execute('''
                UPDATE empleados 
                SET nombre = ?, apellidos = ?, puesto = ?, departamento = ?, activo = ?
                WHERE id = ?
            ''', (nombre, apellidos, puesto, departamento, activo, empleado_id))
            
            conn.commit()
            flash(f'Empleado {nombre} {apellidos} actualizado exitosamente', 'success')
        except Exception as e:
            flash(f'Error al actualizar empleado: {str(e)}', 'error')
        
        conn.close()
        return redirect(url_for('lista_empleados'))
    
    # GET - mostrar formulario
    cursor.execute('SELECT * FROM empleados WHERE id = ?', (empleado_id,))
    empleado = cursor.fetchone()
    conn.close()
    
    if not empleado:
        flash('Empleado no encontrado', 'error')
        return redirect(url_for('lista_empleados'))
    
    return jsonify({
        'success': True,
        'empleado': {
            'id': empleado[0],
            'nombre': empleado[1],
            'apellidos': empleado[2],
            'curp': empleado[3],
            'puesto': empleado[4],
            'departamento': empleado[5],
            'activo': empleado[7]
        }
    })

@app.route('/asistencia')
@login_required
def control_asistencia():
    return render_template('control_asistencia.html')

@app.route('/registrar_asistencia', methods=['POST'])
@login_required
def registrar_asistencia():
    codigo_qr = request.json.get('codigo_qr')
    tipo_registro = request.json.get('tipo', 'entrada')
    
    try:
        # Decodificar código QR
        if not codigo_qr.startswith('EMP_'):
            return jsonify({'success': False, 'message': 'Código QR inválido'})
        
        partes = codigo_qr.split('_')
        empleado_id = int(partes[1])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar empleado
        cursor.execute('SELECT nombre, apellidos FROM empleados WHERE id = ? AND activo = 1', (empleado_id,))
        empleado = cursor.fetchone()
        
        if not empleado:
            return jsonify({'success': False, 'message': 'Empleado no encontrado o inactivo'})
        
        hoy = date.today()
        ahora = datetime.now().strftime('%H:%M:%S')
        
        # Buscar registro del día
        cursor.execute('SELECT id, hora_entrada, hora_salida FROM asistencias WHERE empleado_id = ? AND fecha = ?', 
                      (empleado_id, hoy))
        registro = cursor.fetchone()
        
        if tipo_registro == 'entrada':
            if registro and registro[1]:
                return jsonify({'success': False, 'message': 'Ya se registró la entrada de hoy'})
            
            if registro:
                cursor.execute('UPDATE asistencias SET hora_entrada = ? WHERE id = ?', (ahora, registro[0]))
            else:
                cursor.execute('INSERT INTO asistencias (empleado_id, fecha, hora_entrada) VALUES (?, ?, ?)',
                             (empleado_id, hoy, ahora))
            
            mensaje = f'Entrada registrada para {empleado[0]} {empleado[1]} a las {ahora}'
            
        else:  # salida
            if not registro or not registro[1]:
                return jsonify({'success': False, 'message': 'Debe registrar primero la entrada'})
            
            if registro[2]:
                return jsonify({'success': False, 'message': 'Ya se registró la salida de hoy'})
            
            cursor.execute('UPDATE asistencias SET hora_salida = ? WHERE id = ?', (ahora, registro[0]))
            mensaje = f'Salida registrada para {empleado[0]} {empleado[1]} a las {ahora}'
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': mensaje})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/reportes')
@login_required
def reportes():
    fecha_inicio = request.args.get('fecha_inicio', date.today().strftime('%Y-%m-%d'))
    fecha_fin = request.args.get('fecha_fin', date.today().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.nombre, e.apellidos, e.puesto, e.departamento,
               a.fecha, a.hora_entrada, a.hora_salida, a.observaciones
        FROM asistencias a
        JOIN empleados e ON a.empleado_id = e.id
        WHERE a.fecha BETWEEN ? AND ?
        ORDER BY a.fecha DESC, e.nombre, e.apellidos
    ''', (fecha_inicio, fecha_fin))
    
    asistencias = cursor.fetchall()
    conn.close()
    
    return render_template('reportes.html', 
                         asistencias=asistencias,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin)

# Función para verificar estructura de archivos
def verificar_estructura():
    """Verificar que existan las carpetas y archivos necesarios"""
    carpetas_necesarias = ['templates', 'static', 'static/css', 'static/js', 'database']
    archivos_necesarios = [
        'templates/base.html',
        'templates/login.html', 
        'templates/dashboard.html',
        'templates/registro_personal.html',
        'templates/control_asistencia.html',
        'templates/reportes.html',
        'static/css/styles.css',
        'static/js/main.js'
    ]
    
    print("🔍 Verificando estructura de archivos...")
    
    # Verificar carpetas
    for carpeta in carpetas_necesarias:
        if not os.path.exists(carpeta):
            print(f"❌ Falta la carpeta: {carpeta}")
            os.makedirs(carpeta, exist_ok=True)
            print(f"✅ Carpeta creada: {carpeta}")
        else:
            print(f"✅ Carpeta existe: {carpeta}")
    
    # Verificar archivos
    for archivo in archivos_necesarios:
        if not os.path.exists(archivo):
            print(f"❌ Falta el archivo: {archivo}")
        else:
            print(f"✅ Archivo existe: {archivo}")
    
    print("🔍 Verificación completada.")

if __name__ == '__main__':
    # Verificar estructura antes de iniciar
    verificar_estructura()
    
    # Crear directorio de base de datos si no existe
    os.makedirs('database', exist_ok=True)
    init_db()
    
    print("🚀 Iniciando servidor Flask...")
    print("📍 URL: http://localhost:5000")
    print("👤 Usuario: admin")
    print("🔑 Contraseña: admin2025")
    
    app.run(debug=True, host='0.0.0.0', port=5000)