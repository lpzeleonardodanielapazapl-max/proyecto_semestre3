# utils/auth.py - VERSIÓN CORREGIDA CON DEBUG
import bcrypt
from flask import session, request, redirect, url_for, flash
from functools import wraps
from .conexion import db

# ======================================================
# TABLA HASH
# ======================================================
tabla_hash_usuarios = {}
tabla_hash_clientes = {}


def _is_bcrypt_hash(value):
    return isinstance(value, str) and value.startswith(('$2a$', '$2b$', '$2y$'))


def _normalize_usuario(usuario):
    usuario['ci'] = usuario.get('ci') or usuario.get('nombre_usuario') or str(usuario.get('id_usuario'))
    usuario['email'] = usuario.get('email')
    usuario['nombre_usuario'] = usuario.get('nombre_usuario') or usuario['ci']
    usuario['rol'] = usuario.get('rol')
    usuario['id_sucursal'] = usuario.get('id_sucursal')

    if not usuario.get('nombre'):
        usuario['nombre'] = usuario.get('nombres') or usuario.get('nombre_usuario') or ''
    if not usuario.get('apellido_paterno'):
        usuario['apellido_paterno'] = usuario.get('apellidos') or ''
    if not usuario.get('password_hash'):
        usuario['password_hash'] = usuario.get('contrasena') or ''

    return usuario


def cargar_tabla_hash_usuarios():
    """Carga todos los usuarios a la tabla hash"""
    global tabla_hash_usuarios
    tabla_hash_usuarios = {}

    query = "SELECT * FROM usuario"
    usuarios = db.execute_query(query)

    if usuarios:
        for usuario in usuarios:
            usuario = _normalize_usuario(usuario)
            tabla_hash_usuarios[usuario['nombre_usuario']] = usuario
            if usuario.get('ci'):
                tabla_hash_usuarios[usuario['ci']] = usuario
            if usuario.get('email'):
                tabla_hash_usuarios[usuario['email']] = usuario
            if usuario.get('id_usuario') is not None:
                tabla_hash_usuarios[str(usuario['id_usuario'])] = usuario

    print(f"📋 Tabla Hash cargada con {len(tabla_hash_usuarios)} entradas")
    return usuarios


def cargar_tabla_hash_clientes():
    """Carga todos los clientes a la tabla hash"""
    global tabla_hash_clientes
    tabla_hash_clientes = {}

    query = "SELECT * FROM cliente"
    clientes = db.execute_query(query)

    if clientes:
        for cliente in clientes:
            cliente['nombre'] = cliente.get('nombre') or cliente.get('nombres') or ''
            cliente['apellido_paterno'] = cliente.get('apellido_paterno') or cliente.get('apellidos') or ''
            tabla_hash_clientes[cliente['ci']] = cliente
            if cliente.get('email'):
                tabla_hash_clientes[cliente['email']] = cliente

    print(f"📋 Tabla Hash de clientes cargada con {len(tabla_hash_clientes)} entradas")
    return clientes

def verificar_usuario_hash(identificador, password):
    """Verifica credenciales usando la tabla hash primero"""
    print(f"🔍 Verificando usuario: {identificador}")
    if not identificador:
        return None

    clave = str(identificador).strip()
    usuario = tabla_hash_usuarios.get(clave) or tabla_hash_usuarios.get(clave.lower()) or tabla_hash_usuarios.get(clave.upper())

    if not usuario:
        print(f"❌ Usuario no encontrado: {identificador}")
        return None

    password_hash = usuario.get('password_hash') or ''
    print(f"✅ Usuario encontrado: {usuario.get('nombre_usuario')}")
    print(f"   Credential stored type: {'bcrypt' if _is_bcrypt_hash(password_hash) else 'texto plano'}")

    if _is_bcrypt_hash(password_hash):
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                print(f"❌ Contraseña incorrecta para {usuario.get('nombre_usuario')}")
                return None
        except Exception as e:
            print(f"❌ Error verificando contraseña: {e}")
            return None
    else:
        if password != password_hash:
            print(f"❌ Contraseña incorrecta para {usuario.get('nombre_usuario')}")
            return None

    return {
        'id_usuario': usuario.get('id_usuario'),
        'nombre_usuario': usuario.get('nombre_usuario'),
        'ci': usuario.get('ci'),
        'email': usuario.get('email'),
        'nombre': usuario.get('nombre'),
        'apellido_paterno': usuario.get('apellido_paterno'),
        'rol': usuario.get('rol'),
        'id_sucursal': usuario.get('id_sucursal')
    }


def verificar_cliente_hash(identificador, password):
    """Verifica cliente usando la tabla hash y bcrypt"""
    if not identificador or not password:
        return None

    clave = str(identificador).strip()
    cliente = tabla_hash_clientes.get(clave) or tabla_hash_clientes.get(clave.lower()) or tabla_hash_clientes.get(clave.upper())

    if cliente:
        contrasena_hash = cliente.get('contrasena') or ''
        print(f"✅ Cliente encontrado en Hash: {cliente.get('nombre')}")
        
        if _is_bcrypt_hash(contrasena_hash):
            try:
                if not bcrypt.checkpw(password.encode('utf-8'), contrasena_hash.encode('utf-8')):
                    print(f"❌ Contraseña incorrecta para cliente: {identificador}")
                    return None
            except Exception as e:
                print(f"❌ Error verificando contraseña de cliente: {e}")
                return None
        else:
            # Fallback a texto plano por si acaso
            if password != contrasena_hash:
                print(f"❌ Contraseña incorrecta (plano) para cliente: {identificador}")
                return None
                
        return {
            'id_cliente': cliente.get('id_cliente'),
            'ci': cliente.get('ci'),
            'nombre': cliente.get('nombre') or cliente.get('nombres') or '',
            'apellido_paterno': cliente.get('apellido_paterno') or cliente.get('apellidos') or '',
            'email': cliente.get('email'),
            'telefono': cliente.get('telefono'),
            'direccion': cliente.get('direccion')
        }

    print(f"❌ Cliente no encontrado en Hash: {identificador}")
    return None

def registrar_cliente(ci, nombre, apellido_paterno, apellido_materno, email, telefono, direccion, contrasena):
    """Registra un nuevo cliente en la BD con contrasena encriptada y actualiza tabla hash"""
    apellidos = f"{apellido_paterno} {apellido_materno or ''}".strip()
    
    # Encriptar contraseña con bcrypt
    salt = bcrypt.gensalt(12)
    contrasena_hash = bcrypt.hashpw(contrasena.encode('utf-8'), salt).decode('utf-8')
    
    query = """
        INSERT INTO cliente (ci, nombres, apellidos, email, telefono, direccion, contrasena)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    params = (ci, nombre, apellidos, email, telefono, direccion, contrasena_hash)
    resultado = db.execute_insert(query, params)
    
    if resultado:
        cargar_tabla_hash_clientes()
        return resultado
    
    return None

def login_user(user_data, es_cliente=False):
    """Inicia sesión para un usuario o cliente"""
    if es_cliente:
        session.clear()
        session['cliente_id'] = user_data['id_cliente']
        session['cliente_nombre'] = f"{user_data['nombre']} {user_data['apellido_paterno']}"
        session['cliente_ci'] = user_data['ci']
        session['cliente_email'] = user_data['email']
        session['tipo_usuario'] = 'cliente'
        session['logged_in'] = True
        print(f"✅ Sesión iniciada para CLIENTE: {user_data['nombre']}")
    else:
        session.clear()
        session['user_id'] = user_data['id_usuario']
        session['user_nombre'] = f"{user_data['nombre']} {user_data['apellido_paterno']}"
        session['user_ci'] = user_data['ci']
        session['user_email'] = user_data['email']
        session['rol'] = user_data['rol']
        session['sucursal_id'] = user_data.get('id_sucursal')
        session['tipo_usuario'] = 'admin'
        session['logged_in'] = True
        print(f"✅ Sesión iniciada para ADMIN: {user_data['nombre']} (Rol: {user_data['rol']})")

def logout_user():
    """Cierra la sesión"""
    session.clear()
    flash('Sesión cerrada correctamente', 'info')

def get_current_user():
    """Obtiene los datos del usuario actual"""
    if 'user_id' in session:
        query = "SELECT id_usuario, ci, nombre, apellido_paterno, email, rol, id_sucursal FROM usuario WHERE id_usuario = %s"
        result = db.execute_query(query, (session['user_id'],))
        return result[0] if result else None
    return None

def get_current_cliente():
    """Obtiene los datos del cliente actual"""
    if 'cliente_id' in session:
        query = "SELECT id_cliente, ci, nombre, apellido_paterno, email, telefono, direccion FROM cliente WHERE id_cliente = %s"
        result = db.execute_query(query, (session['cliente_id'],))
        return result[0] if result else None
    return None

# ======================================================
# DECORADORES PARA RUTAS
# ======================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Por favor, inicia sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def rol_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash('Por favor, inicia sesión', 'warning')
                return redirect(url_for('login'))
            if session.get('tipo_usuario') != 'admin':
                flash('Acceso denegado. No tienes permisos suficientes.', 'danger')
                return redirect(url_for('cliente_dashboard'))
            if session.get('rol') not in roles:
                flash('Acceso denegado. No tienes permisos suficientes.', 'danger')
                return redirect(url_for('admin_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return rol_required('ADMIN')(f)

def farmaceutico_required(f):
    return rol_required('ADMIN', 'FARMACEUTICO')(f)

def cajero_required(f):
    return rol_required('ADMIN', 'CAJERO')(f)

# ======================================================
# INICIALIZAR
# ======================================================
# La carga de usuarios y clientes ahora se realiza desde app.py durante
# la inicialización del sistema para evitar dependencias de base de datos
# en el momento de importar el módulo.
