# ======================================================
# APLICACIÓN PRINCIPAL - FARMACIAS BOLIVIA
# SISTEMA DE GESTIÓN INTEGRAL
# ======================================================

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_session import Session
import os
from datetime import datetime

# Importar configuraciones
from config import Config

# Importar utilidades
from utils.conexion import db, test_connection
from utils.auth import (
    login_user, logout_user, get_current_user, get_current_cliente,
    verificar_usuario_hash, verificar_cliente_hash,
    registrar_cliente, cargar_tabla_hash_usuarios, cargar_tabla_hash_clientes,
    login_required, admin_required, farmaceutico_required, cajero_required
)

# Importar estructuras de datos
from estructura_datos import (
    ListaEnlazadaCarrito, ColaPedidos, PilaHistorial,
    ArbolBinarioMedicamentos, TablaHashUsuarios, GestionEstructuras
)

# Crear aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)
Session(app)

# Configurar carpeta de uploads con ruta absoluta
upload_folder = app.config['UPLOAD_FOLDER']
if not os.path.isabs(upload_folder):
    upload_folder = os.path.join(app.root_path, upload_folder)
app.config['UPLOAD_FOLDER'] = upload_folder
os.makedirs(upload_folder, exist_ok=True)

# Instancia global de estructuras de datos
estructuras = GestionEstructuras()
initialized = False


# ======================================================
# FUNCIONES AUXILIARES
# ======================================================

def archivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cargar_medicamentos_al_arbol():
    query = """
        SELECT m.id_medicamento, m.nombre_comercial, m.nombre_generico,
               m.precio_actual, COALESCE(SUM(i.stock_actual), 0) as stock_actual
        FROM medicamento m
        LEFT JOIN inventario i ON m.id_medicamento = i.id_medicamento
        GROUP BY m.id_medicamento
    """
    medicamentos = db.execute_query(query)
    print(f"📊 Medicamentos encontrados en BD: {len(medicamentos) if medicamentos else 0}")
    
    if medicamentos:
        for med in medicamentos:
            estructuras.arbol_medicamentos.insertar(
                med['id_medicamento'],
                med['nombre_comercial'],
                med.get('nombre_generico', ''),
                float(med['precio_actual']),
                med.get('stock_actual', 0)
            )
        print(f"✅ {len(medicamentos)} medicamentos cargados al árbol binario")
    else:
        print("⚠️ No se encontraron medicamentos en la BD")
    
    return medicamentos

def cargar_usuarios_al_hash():
    query = "SELECT * FROM usuario"
    usuarios = db.execute_query(query)
    print(f"📊 Usuarios encontrados en BD: {len(usuarios) if usuarios else 0}")
    
    if usuarios:
        for user in usuarios:
            if user.get('ci') is None:
                user['ci'] = user.get('nombre_usuario')
            estructuras.tabla_usuarios.insertar(user.get('nombre_usuario') or user['ci'], user)
            if user.get('ci'):
                estructuras.tabla_usuarios.insertar(user['ci'], user)
            if user.get('email'):
                estructuras.tabla_usuarios.insertar(user['email'], user)
        print(f"✅ {len(usuarios)} usuarios cargados a la tabla hash")
    else:
        print("⚠️ No se encontraron usuarios en la BD")
    
    return usuarios


# ======================================================
# INICIALIZACIÓN DEL SISTEMA
# ======================================================

@app.before_request
def inicializar_sistema():
    global initialized
    if initialized:
        return
    initialized = True

    print("=" * 60)
    print("🚀 INICIANDO FARMACIAS BOLIVIA - SISTEMA DE GESTIÓN")
    print("=" * 60)
    
    if test_connection():
        print("✅ Base de datos conectada")
        
        cargar_tabla_hash_usuarios()
        cargar_tabla_hash_clientes()
        medicamentos = cargar_medicamentos_al_arbol()
        usuarios = cargar_usuarios_al_hash()
        
        try:
            pedidos = db.execute_query("SELECT * FROM vista_pedidos_pendientes")
        except Exception:
            pedidos = db.execute_query("""
                SELECT p.*, p.fecha AS fecha_pedido, p.estado AS estado_pedido
                FROM pedido p
                WHERE p.estado = 'PENDIENTE'
            """) or []

        for pedido in pedidos:
            if 'fecha' in pedido and 'fecha_pedido' not in pedido:
                pedido['fecha_pedido'] = pedido['fecha']
            if 'estado' in pedido and 'estado_pedido' not in pedido:
                pedido['estado_pedido'] = pedido['estado']

        if pedidos:
            for pedido in pedidos:
                estructuras.cola_pedidos.encolar(pedido)
            print(f"✅ {len(pedidos)} pedidos cargados a la cola FIFO")
        else:
            print("✅ No hay pedidos pendientes")
        
        print("-" * 60)
        print(str(estructuras))
        print("-" * 60)
    else:
        print("❌ Error de conexión a la base de datos")
    
    print("🎯 SISTEMA LISTO PARA USAR")
    print("=" * 60)


# ======================================================
# RUTAS PRINCIPALES
# ======================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        if session.get('tipo_usuario') == 'admin':
            rol = session.get('rol')
            if rol == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            elif rol == 'FARMACEUTICO':
                return redirect(url_for('admin_pedidos'))
            elif rol == 'CAJERO':
                return redirect(url_for('admin_ventas'))
        else:
            return redirect(url_for('cliente_dashboard'))
    
    if request.method == 'POST':
        identificador = request.form.get('identificador')
        identificador = identificador.strip() if identificador else ''
        password = request.form.get('password') or ''
        tipo = request.form.get('tipo', 'admin')
        
        print(f"📝 Intento de login: {identificador} - Tipo: {tipo}")
        
        if tipo == 'admin':
            usuario = verificar_usuario_hash(identificador, password)
            if usuario:
                login_user(usuario, es_cliente=False)
                estructuras.registrar_accion('INICIO_SESION', 'AUTH', 
                                            f'Usuario {usuario["nombre"]} inició sesión')
                flash(f'¡Bienvenido {usuario["nombre"]}!', 'success')
                
                if usuario['rol'] == 'ADMIN':
                    return redirect(url_for('admin_dashboard'))
                elif usuario['rol'] == 'FARMACEUTICO':
                    return redirect(url_for('admin_pedidos'))
                else:
                    return redirect(url_for('admin_ventas'))
            else:
                print(f"❌ Login fallido para: {identificador}")
                flash('Credenciales inválidas', 'danger')
        else:
            cliente = verificar_cliente_hash(identificador, password)
            if cliente:
                login_user(cliente, es_cliente=True)
                estructuras.registrar_accion('INICIO_SESION', 'AUTH', 
                                            f'Cliente {cliente["nombre"]} inició sesión')
                flash(f'¡Bienvenido {cliente["nombre"]}!', 'success')
                return redirect(url_for('cliente_dashboard'))
            else:
                flash('Credenciales inválidas o cliente no registrado', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/registro', methods=['GET', 'POST'])
def registro_cliente():
    if request.method == 'POST':
        ci = request.form.get('ci')
        nombre = request.form.get('nombre')
        apellido_paterno = request.form.get('apellido_paterno')
        apellido_materno = request.form.get('apellido_materno')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        contrasena = request.form.get('contrasena')
        
        query = "SELECT * FROM cliente WHERE ci = %s OR email = %s"
        existe = db.execute_query(query, (ci, email))
        
        if existe:
            flash('Ya existe un cliente con esa CI o email', 'danger')
            return redirect(url_for('registro_cliente'))
        
        resultado = registrar_cliente(ci, nombre, apellido_paterno, apellido_materno, 
                                       email, telefono, direccion, contrasena)
        
        if resultado:
            flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error al registrar. Intenta nuevamente.', 'danger')
    
    return render_template('registro_cliente.html')


# ======================================================
# RUTAS ADMINISTRATIVAS
# ======================================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session.get('tipo_usuario') != 'admin':
        return redirect(url_for('cliente_dashboard'))
    
    hoy = datetime.now().date()
    inicio_mes = hoy.replace(day=1)
    
    query_ventas = """
        SELECT COUNT(*) as total_ventas, COALESCE(SUM(total), 0) as monto_total
        FROM venta WHERE DATE(fecha) = %s
    """
    ventas_hoy = db.execute_query(query_ventas, (hoy,))
    
    stock_critico = db.execute_query("SELECT COUNT(*) as total FROM vw_stock_critico")
    
    query_clientes = """
        SELECT COUNT(*) as nuevos_clientes 
        FROM cliente WHERE DATE(fecha_registro) >= %s
    """
    clientes_nuevos = db.execute_query(query_clientes, (inicio_mes,))
    
    query_ganancias = """
        SELECT COALESCE(SUM(total), 0) as ganancia_mes
        FROM venta WHERE DATE(fecha) >= %s
    """
    ganancias_mes = db.execute_query(query_ganancias, (inicio_mes,))
    
    pedidos_pendientes = db.execute_query("SELECT COUNT(*) as total FROM pedido WHERE estado = 'PENDIENTE'")
    
    context = {
        'ventas_hoy': ventas_hoy[0] if ventas_hoy else {'total_ventas': 0, 'monto_total': 0},
        'stock_critico': stock_critico[0]['total'] if stock_critico else 0,
        'clientes_nuevos': clientes_nuevos[0]['nuevos_clientes'] if clientes_nuevos else 0,
        'ganancias_mes': ganancias_mes[0]['ganancia_mes'] if ganancias_mes else 0,
        'pedidos_pendientes': pedidos_pendientes[0]['total'] if pedidos_pendientes else 0,
        'estructuras': estructuras.estado_completo()
    }
    
    return render_template('admin/dashboard.html', **context)

@app.route('/admin/ventas')
@login_required
def admin_ventas():
    if session.get('tipo_usuario') != 'admin':
        return redirect(url_for('cliente_dashboard'))
    
    rol = session.get('rol')
    if rol not in ['ADMIN', 'CAJERO']:
        flash('No tienes permisos para acceder a ventas', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    query = """
        SELECT v.*, s.nombre as sucursal_nombre
        FROM venta v
        JOIN sucursal s ON v.id_sucursal = s.id_sucursal
        ORDER BY v.fecha DESC
        LIMIT 100
    """
    ventas = db.execute_query(query)
    
    return render_template('admin/ventas.html', ventas=ventas)

@app.route('/admin/inventario')
@login_required
def admin_inventario():
    if session.get('tipo_usuario') != 'admin':
        return redirect(url_for('cliente_dashboard'))
    
    rol = session.get('rol')
    if rol not in ['ADMIN', 'FARMACEUTICO']:
        flash('No tienes permisos para acceder a inventario', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    query = """
        SELECT i.*, m.nombre_comercial, m.nombre_generico, i.stock_minimo,
               s.nombre as sucursal_nombre
        FROM inventario i
        JOIN medicamento m ON i.id_medicamento = m.id_medicamento
        JOIN sucursal s ON i.id_sucursal = s.id_sucursal
        ORDER BY s.nombre, m.nombre_comercial
    """
    inventario = db.execute_query(query)
    
    try:
        stock_critico = db.execute_query("SELECT * FROM vw_stock_critico")
    except Exception:
        stock_critico = []

    try:
        proximos_vencer = db.execute_query("SELECT * FROM vista_proximos_vencer LIMIT 10")
    except Exception:
        proximos_vencer = []
    
    return render_template('admin/inventario.html', 
                          inventario=inventario, 
                          stock_critico=stock_critico,
                          proximos_vencer=proximos_vencer)

@app.route('/admin/pedidos')
@login_required
def admin_pedidos():
    if session.get('tipo_usuario') != 'admin':
        return redirect(url_for('cliente_dashboard'))
    
    rol = session.get('rol')
    if rol not in ['ADMIN', 'FARMACEUTICO']:
        flash('No tienes permisos para acceder a pedidos', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        pedidos = db.execute_query("SELECT * FROM vista_pedidos_pendientes")
    except Exception:
        pedidos = db.execute_query("""
            SELECT p.*, p.fecha AS fecha_pedido, p.estado AS estado_pedido
            FROM pedido p
            WHERE p.estado = 'PENDIENTE'
        """) or []

    for pedido in pedidos:
        if 'fecha' in pedido and 'fecha_pedido' not in pedido:
            pedido['fecha_pedido'] = pedido['fecha']
        if 'estado' in pedido and 'estado_pedido' not in pedido:
            pedido['estado_pedido'] = pedido['estado']

    if estructuras.cola_pedidos.esta_vacia() and pedidos:
        for pedido in pedidos:
            estructuras.cola_pedidos.encolar(pedido)
    
    return render_template('admin/pedidos.html', 
                          pedidos=pedidos, 
                          cola_pedidos=estructuras.cola_pedidos)

@app.route('/admin/clientes')
@login_required
def admin_clientes():
    if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    query = "SELECT * FROM cliente ORDER BY fecha_registro DESC"
    clientes = db.execute_query(query)
    
    return render_template('admin/clientes.html', clientes=clientes)

@app.route('/admin/medicamentos')
@login_required
def admin_medicamentos():
    if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    query = """
        SELECT m.*, m.precio_actual AS precio_venta,
               (SELECT SUM(stock_actual) FROM inventario WHERE id_medicamento = m.id_medicamento) as stock_total
        FROM medicamento m
        ORDER BY m.nombre_comercial
    """
    medicamentos = db.execute_query(query)
    
    return render_template('admin/medicamentos.html', medicamentos=medicamentos)

@app.route('/admin/reportes')
@login_required
def admin_reportes():
    if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # 1. Top Products
    try:
        top_productos = db.execute_query("""
            SELECT m.nombre_comercial, m.nombre_generico, SUM(dv.cantidad) AS unidades_vendidas, 
                   COUNT(DISTINCT dv.id_venta) AS numero_ventas, SUM(dv.subtotal) AS ingreso_total
            FROM detalle_venta dv
            JOIN medicamento m ON dv.id_medicamento = m.id_medicamento
            GROUP BY m.id_medicamento, m.nombre_comercial, m.nombre_generico
            ORDER BY unidades_vendidas DESC LIMIT 10
        """)
    except Exception as e:
        print(f"Error top_productos: {e}")
        top_productos = []

    # 2. Clientes Frecuentes
    try:
        clientes_frecuentes = db.execute_query("""
            SELECT c.id_cliente, c.ci, CONCAT(c.nombres, ' ', c.apellidos) AS nombre_completo, 
                   COUNT(p.id_pedido) AS total_compras, SUM(p.total) AS monto_total_gastado,
                   AVG(p.total) AS ticket_promedio
            FROM cliente c
            JOIN pedido p ON c.id_cliente = p.id_cliente
            WHERE p.estado = 'ENTREGADO'
            GROUP BY c.id_cliente, c.ci, c.nombres, c.apellidos
            ORDER BY monto_total_gastado DESC
            LIMIT 10
        """)
    except Exception as e:
        print(f"Error clientes_frecuentes: {e}")
        clientes_frecuentes = []

    # 3. Valorización Inventario
    try:
        valorizacion = db.execute_query("""
            SELECT s.nombre AS sucursal, 
                   COUNT(DISTINCT i.id_medicamento) AS total_productos,
                   SUM(i.stock_actual) AS total_unidades,
                   SUM(i.stock_actual * COALESCE((SELECT AVG(dc.precio_compra) FROM detalle_compra dc WHERE dc.id_medicamento = i.id_medicamento), m.precio_actual * 0.70)) AS valor_costo,
                   SUM(i.stock_actual * m.precio_actual) AS valor_venta,
                   SUM(i.stock_actual * (m.precio_actual - COALESCE((SELECT AVG(dc.precio_compra) FROM detalle_compra dc WHERE dc.id_medicamento = i.id_medicamento), m.precio_actual * 0.70))) AS ganancia_potencial
            FROM inventario i
            JOIN sucursal s ON i.id_sucursal = s.id_sucursal
            JOIN medicamento m ON i.id_medicamento = m.id_medicamento
            GROUP BY s.id_sucursal, s.nombre
        """)
    except Exception as e:
        print(f"Error valorizacion: {e}")
        valorizacion = []
    
    return render_template('admin/reportes.html',
                          top_productos=top_productos,
                          clientes_frecuentes=clientes_frecuentes,
                          valorizacion=valorizacion)

@app.route('/admin/sucursales')
@login_required
def admin_sucursales():
    if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    query = "SELECT *, TRUE as activa FROM sucursal ORDER BY nombre"
    sucursales = db.execute_query(query)
    
    return render_template('admin/sucursales.html', sucursales=sucursales)


# ======================================================
# RUTAS DE CLIENTE
# ======================================================
@app.route('/cliente/dashboard')
@login_required
def cliente_dashboard():
    if session.get('tipo_usuario') != 'cliente':
        return redirect(url_for('login'))
    
    cliente_id = session['cliente_id']
    
    # Últimos pedidos
    query_pedidos = """
        SELECT p.*, p.fecha AS fecha_pedido, p.estado AS estado_pedido
        FROM pedido p
        WHERE p.id_cliente = %s 
        ORDER BY p.fecha DESC 
        LIMIT 5
    """
    pedidos = db.execute_query(query_pedidos, (cliente_id,))
    
    # Total gastado
    query_total = """
        SELECT COALESCE(SUM(total), 0) as total_gastado
        FROM pedido 
        WHERE id_cliente = %s AND estado IN ('ENTREGADO', 'COMPLETADO', 'CONFIRMADO', 'PREPARANDO', 'ENVIADO')
    """
    total_gastado = db.execute_query(query_total, (cliente_id,))
    total_gastado_val = total_gastado[0]['total_gastado'] if total_gastado else 0
    
    # Pedidos pendientes
    query_pendientes = """
        SELECT COUNT(*) as pendientes
        FROM pedido 
        WHERE id_cliente = %s AND estado = 'PENDIENTE'
    """
    pedidos_pendientes = db.execute_query(query_pendientes, (cliente_id,))
    pendientes_val = pedidos_pendientes[0]['pendientes'] if pedidos_pendientes else 0
    
    # Recomendaciones
    recomendaciones = db.execute_query("""
        SELECT m.*, m.precio_actual AS precio_venta
        FROM medicamento m
        ORDER BY RAND() 
        LIMIT 4
    """)
    
    print(f"📊 Dashboard cliente {cliente_id}: Total gastado = {total_gastado_val}, Pedidos pendientes = {pendientes_val}")
    
    return render_template('cliente/dashboard.html', 
                          pedidos=pedidos, 
                          recomendaciones=recomendaciones,
                          total_gastado=total_gastado_val,
                          pedidos_pendientes=pendientes_val)

@app.route('/cliente/catalogo')
@login_required
def cliente_catalogo():
    if session.get('tipo_usuario') != 'cliente':
        return redirect(url_for('login'))
    
    search = request.args.get('search', '')
    
    if search:
        medicamentos = estructuras.arbol_medicamentos.buscar_por_prefijo(search)
    else:
        query = """
            SELECT m.*, m.precio_actual AS precio_venta, COALESCE(SUM(i.stock_actual), 0) as stock
            FROM medicamento m
            LEFT JOIN inventario i ON m.id_medicamento = i.id_medicamento
            GROUP BY m.id_medicamento
            ORDER BY m.nombre_comercial
        """
        medicamentos = db.execute_query(query)
    
    return render_template('cliente/catalogo.html', medicamentos=medicamentos, search=search)

@app.route('/cliente/carrito')
@login_required
def cliente_carrito():
    if session.get('tipo_usuario') != 'cliente':
        return redirect(url_for('login'))
    
    items = estructuras.carrito.obtener_todos()
    total = estructuras.carrito.obtener_total()
    
    return render_template('cliente/carrito.html', items=items, total=total)

@app.route('/cliente/checkout', methods=['GET', 'POST'])
@login_required
def cliente_checkout():
    if session.get('tipo_usuario') != 'cliente':
        return redirect(url_for('login'))
    
    items = estructuras.carrito.obtener_todos()
    subtotal = estructuras.carrito.obtener_total()
    iva = subtotal * 0.13
    total = subtotal + iva
    
    print(f"🔍 Carrito checkout - Items: {len(items)}")
    print(f"🔍 Subtotal: {subtotal}, IVA: {iva}, Total: {total}")
    
    if len(items) == 0:
        flash('No hay productos en el carrito', 'warning')
        return redirect(url_for('cliente_carrito'))
        
    # Query branches
    sucursales = db.execute_query("SELECT id_sucursal, nombre, direccion, ciudad FROM sucursal ORDER BY nombre") or []
    
    # Check if prescription required
    requiere_receta = any(item.get('requiere_receta') for item in items)
    
    return render_template('cliente/checkout.html', 
                          items=items, 
                          subtotal=subtotal, 
                          iva=iva, 
                          total=total,
                          sucursales=sucursales,
                          requiere_receta=requiere_receta)

@app.route('/cliente/mis-pedidos')
@login_required
def cliente_mis_pedidos():
    if session.get('tipo_usuario') != 'cliente':
        return redirect(url_for('login'))
    
    cliente_id = session['cliente_id']
    
    query = """
        SELECT p.*, p.fecha AS fecha_pedido, p.estado AS estado_pedido,
               (SELECT COUNT(*) FROM detalle_pedido WHERE id_pedido = p.id_pedido) as total_productos
        FROM pedido p
        WHERE p.id_cliente = %s
        ORDER BY p.fecha DESC
    """
    pedidos = db.execute_query(query, (cliente_id,))
    
    return render_template('cliente/mis_pedidos.html', pedidos=pedidos)

@app.route('/cliente/perfil', methods=['GET', 'POST'])
@login_required
def cliente_perfil():
    if session.get('tipo_usuario') != 'cliente':
        return redirect(url_for('login'))
    
    cliente_id = session['cliente_id']
    
    if request.method == 'POST':
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        
        query = "UPDATE cliente SET telefono = %s, direccion = %s WHERE id_cliente = %s"
        db.execute_update(query, (telefono, direccion, cliente_id))
        
        flash('Perfil actualizado correctamente', 'success')
    
    query = "SELECT * FROM cliente WHERE id_cliente = %s"
    cliente = db.execute_query(query, (cliente_id,))
    
    return render_template('cliente/perfil.html', cliente=cliente[0] if cliente else None)

@app.route('/cliente/favoritos')
@login_required
def cliente_favoritos():
    if session.get('tipo_usuario') != 'cliente':
        return redirect(url_for('login'))
    
    cliente_id = session['cliente_id']
    
    query = """
        SELECT m.*, m.precio_actual AS precio_venta, f.id_favorito
        FROM favoritos f
        JOIN medicamento m ON f.id_medicamento = m.id_medicamento
        WHERE f.id_cliente = %s
    """
    favoritos = db.execute_query(query, (cliente_id,))
    
    return render_template('cliente/favoritos.html', favoritos=favoritos)


# ======================================================
# API PARA ESTRUCTURAS DE DATOS
# ======================================================

@app.route('/api/estructuras/estado')
@login_required
def api_estructuras_estado():
    return jsonify(estructuras.estado_completo())

@app.route('/api/carrito/count')
@login_required
def api_carrito_count():
    return jsonify({'count': len(estructuras.carrito)})

@app.route('/api/carrito/agregar', methods=['POST'])
@login_required
def api_agregar_carrito():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        producto_id = data.get('producto_id')
        nombre = data.get('nombre')
        cantidad = data.get('cantidad', 1)
        precio = data.get('precio')
        requiere_receta = data.get('requiere_receta', False)
        
        if not producto_id or not nombre or not precio:
            return jsonify({'success': False, 'error': 'Faltan datos'}), 400
        
        estructuras.carrito.agregar(producto_id, nombre, cantidad, float(precio), requiere_receta)
        
        print(f"✅ Producto agregado: {nombre} x{cantidad}")
        print(f"📦 Carrito ahora tiene: {len(estructuras.carrito)} items")
        
        estructuras.registrar_accion('AGREGAR_CARRITO', 'COMPRAS', 
                                     f'Agregado {nombre} x{cantidad}')
        
        return jsonify({
            'success': True,
            'carrito_items': len(estructuras.carrito),
            'carrito_total': estructuras.carrito.obtener_total()
        })
    except Exception as e:
        print(f"❌ Error en api_agregar_carrito: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/carrito/actualizar', methods=['POST'])
@login_required
def api_actualizar_carrito():
    try:
        data = request.get_json()
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad')
        
        if not producto_id or not cantidad:
            return jsonify({'success': False, 'error': 'Faltan datos'}), 400
        
        estructuras.carrito.actualizar_cantidad(producto_id, cantidad)
        
        return jsonify({
            'success': True,
            'carrito_items': len(estructuras.carrito),
            'carrito_total': estructuras.carrito.obtener_total()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/carrito/eliminar', methods=['POST'])
@login_required
def api_eliminar_carrito():
    try:
        data = request.get_json()
        producto_id = data.get('producto_id')
        
        if not producto_id:
            return jsonify({'success': False, 'error': 'Faltan datos'}), 400
        
        estructuras.carrito.eliminar(producto_id)
        
        return jsonify({
            'success': True,
            'carrito_items': len(estructuras.carrito),
            'carrito_total': estructuras.carrito.obtener_total()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pedidos/crear', methods=['POST'])
@login_required
def api_crear_pedido():
    print("=" * 50)
    print("🔵 API crear pedido - INICIANDO (MÓDULO RECETA Y MULTIPART)")
    
    try:
        if session.get('tipo_usuario') != 'cliente':
            print("❌ Error: Usuario no es cliente")
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
        
        # Check if request has files (multipart form)
        if request.files or 'multipart/form-data' in (request.content_type or ''):
            direccion = request.form.get('direccion')
            id_sucursal_despacho = request.form.get('id_sucursal_despacho')
            metodo_pago = request.form.get('metodo_pago')
            telefono = request.form.get('telefono')
            receta_file = request.files.get('receta_medica')
        else:
            data = request.get_json() or {}
            direccion = data.get('direccion')
            id_sucursal_despacho = data.get('id_sucursal_despacho')
            metodo_pago = data.get('metodo_pago')
            telefono = data.get('telefono')
            receta_file = None
            
        print(f"📦 Datos extraídos: direccion={direccion}, sucursal={id_sucursal_despacho}, metodo={metodo_pago}, telefono={telefono}, archivo={receta_file}")
        
        if not direccion:
            return jsonify({'success': False, 'error': 'Falta dirección de entrega'}), 400
        
        if not metodo_pago:
            return jsonify({'success': False, 'error': 'Falta método de pago'}), 400
            
        if not id_sucursal_despacho:
            return jsonify({'success': False, 'error': 'Falta sucursal de despacho'}), 400

        if metodo_pago not in Config.METODOS_PAGO:
            return jsonify({'success': False, 'error': 'Método de pago inválido'}), 400

        items = estructuras.carrito.obtener_todos()
        if len(items) == 0:
            return jsonify({'success': False, 'error': 'El carrito está vacío'}), 400
        
        # Check if prescription is actually required
        requiere_receta = any(item.get('requiere_receta') for item in items)
        
        receta_url = None
        estado_pedido = 'PENDIENTE'
        
        if requiere_receta:
            if not receta_file or receta_file.filename == '':
                return jsonify({'success': False, 'error': 'Se requiere subir una receta médica para finalizar la compra de este medicamento.'}), 400
            
            if receta_file and archivo_permitido(receta_file.filename):
                from werkzeug.utils import secure_filename
                filename = secure_filename(f"receta_{datetime.now().strftime('%Y%m%d%H%M%S')}_{receta_file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                receta_file.save(file_path)
                # Save relative path for URL retrieval
                receta_url = os.path.join('static/uploads/recetas', filename).replace('\\', '/')
                estado_pedido = 'REVISION_RECETA'
                print(f"📸 Receta guardada en: {file_path}")
            else:
                return jsonify({'success': False, 'error': 'Formato de archivo de receta no permitido'}), 400
        
        subtotal = estructuras.carrito.obtener_total()
        iva = subtotal * 0.13
        total = subtotal + iva
        
        num_pedido = f"PED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        query_pedido = """
            INSERT INTO pedido (id_cliente, id_sucursal_despacho, numero_pedido, subtotal, iva, total, 
                               metodo_pago, direccion_entrega, telefono_contacto, estado, receta_medica_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params_pedido = (session['cliente_id'], id_sucursal_despacho, num_pedido, subtotal, iva, total, 
                        metodo_pago, direccion, telefono if telefono else None, estado_pedido, receta_url)
        
        pedido_id = db.execute_insert(query_pedido, params_pedido)
        
        if not pedido_id:
            return jsonify({'success': False, 'error': 'Error al guardar el pedido'}), 500
        
        for item in items:
            query_detalle = """
                INSERT INTO detalle_pedido (id_pedido, id_medicamento, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """
            params_detalle = (pedido_id, item['producto_id'], item['cantidad'], 
                            item['precio'], item['subtotal'])
            db.execute_insert(query_detalle, params_detalle)
        
        estructuras.cola_pedidos.encolar({
            'id_pedido': pedido_id,
            'numero_pedido': num_pedido,
            'cliente': session.get('cliente_nombre', 'Cliente'),
            'total': total,
            'estado': estado_pedido,
            'fecha': datetime.now().isoformat()
        })
        
        estructuras.registrar_accion('CREAR_PEDIDO', 'CHECKOUT', 
                                     f'Pedido #{num_pedido} por Bs.{total:.2f} (Estado: {estado_pedido})')
        
        estructuras.carrito.vaciar()
        
        return jsonify({
            'success': True,
            'pedido_id': pedido_id,
            'numero_pedido': num_pedido,
            'total': total
        })
        
    except Exception as e:
        print(f"❌ ERROR EN CREAR PEDIDO: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/pedidos/detalle/<int:pedido_id>')
@login_required
def api_pedido_detalle(pedido_id):
    """API para obtener detalles de un pedido"""
    try:
        # Verificar que el pedido pertenece al cliente
        if session.get('tipo_usuario') == 'cliente':
            query_check = "SELECT id_cliente FROM pedido WHERE id_pedido = %s"
            pedido = db.execute_query(query_check, (pedido_id,))
            if not pedido or pedido[0]['id_cliente'] != session.get('cliente_id'):
                return jsonify({'success': False, 'error': 'Acceso denegado'}), 403
        
        # Obtener productos del pedido
        query = """
            SELECT dp.*, m.nombre_comercial
            FROM detalle_pedido dp
            JOIN medicamento m ON dp.id_medicamento = m.id_medicamento
            WHERE dp.id_pedido = %s
        """
        productos = db.execute_query(query, (pedido_id,))
        
        return jsonify({
            'success': True,
            'productos': productos
        })
    except Exception as e:
        print(f"Error en detalle pedido: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    

# ======================================================
# API PARA FARMACEUTICO - PEDIDOS
# ======================================================

@app.route('/api/pedidos/cambiar-estado', methods=['POST'])
@login_required
def api_cambiar_estado_pedido():
    """API para cambiar estado de un pedido"""
    try:
        if session.get('tipo_usuario') != 'admin':
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
        
        rol = session.get('rol')
        if rol not in ['ADMIN', 'FARMACEUTICO']:
            return jsonify({'success': False, 'error': 'No tienes permisos'}), 401
        
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        nuevo_estado = data.get('estado')
        
        if not pedido_id or not nuevo_estado:
            return jsonify({'success': False, 'error': 'Faltan datos'}), 400
        
        # Estados válidos
        estados_validos = ['PENDIENTE', 'REVISION_RECETA', 'CONFIRMADO', 'PREPARANDO', 'ENVIADO', 'ENTREGADO', 'CANCELADO']
        if nuevo_estado not in estados_validos:
            return jsonify({'success': False, 'error': 'Estado no válido'}), 400
        
        # Obtener estado actual
        query_actual = "SELECT estado FROM pedido WHERE id_pedido = %s"
        actual = db.execute_query(query_actual, (pedido_id,))
        
        if not actual:
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
        
        # Normalizar estado
        estado_actual = actual[0]['estado'] or 'PENDIENTE'
        
        # Validar transición
        transiciones = {
            'PENDIENTE': ['REVISION_RECETA', 'CONFIRMADO', 'CANCELADO'],
            'REVISION_RECETA': ['CONFIRMADO', 'CANCELADO'],
            'CONFIRMADO': ['PREPARANDO', 'CANCELADO'],
            'PREPARANDO': ['ENVIADO', 'CANCELADO'],
            'ENVIADO': ['ENTREGADO'],
            'ENTREGADO': [],
            'CANCELADO': []
        }
        
        if nuevo_estado not in transiciones.get(estado_actual, []):
            return jsonify({'success': False, 'error': f'No se puede cambiar de {estado_actual} a {nuevo_estado}'}), 400
        
        # Actualizar estado
        query_update = """
            UPDATE pedido 
            SET estado = %s
            WHERE id_pedido = %s
        """
        db.execute_update(query_update, (nuevo_estado, pedido_id))
        
        # Registrar acción
        estructuras.registrar_accion('CAMBIAR_ESTADO_PEDIDO', 'PEDIDOS', 
                                     f'Pedido {pedido_id} cambiado a {nuevo_estado}')
        
        print(f"✅ Pedido {pedido_id} cambiado de {estado_actual} a {nuevo_estado}")
        
        return jsonify({'success': True, 'mensaje': 'Estado actualizado'})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pedidos/aprobar-receta', methods=['POST'])
@login_required
def api_aprobar_receta():
    try:
        if session.get('tipo_usuario') != 'admin':
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
        
        rol = session.get('rol')
        if rol not in ['ADMIN', 'FARMACEUTICO']:
            return jsonify({'success': False, 'error': 'No tienes permisos de farmacéutico'}), 401
        
        data = request.get_json() or {}
        pedido_id = data.get('pedido_id')
        
        if not pedido_id:
            return jsonify({'success': False, 'error': 'Falta el ID del pedido'}), 400
            
        # Update order status to CONFIRMADO and set farmaceutico auditor
        query = """
            UPDATE pedido
            SET estado = 'CONFIRMADO', id_farmaceutico_auditor = %s
            WHERE id_pedido = %s
        """
        rows = db.execute_update(query, (session['user_id'], pedido_id))
        
        if rows > 0:
            estructuras.registrar_accion('APROBAR_RECETA', 'PEDIDOS', f'Receta aprobada para pedido {pedido_id}')
            return jsonify({'success': True, 'message': 'Receta aprobada con éxito'})
        else:
            return jsonify({'success': False, 'error': 'No se pudo actualizar el pedido'}), 400
    except Exception as e:
        print(f"❌ Error al aprobar receta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pedidos/rechazar-receta', methods=['POST'])
@login_required
def api_rechazar_receta():
    try:
        if session.get('tipo_usuario') != 'admin':
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
        
        rol = session.get('rol')
        if rol not in ['ADMIN', 'FARMACEUTICO']:
            return jsonify({'success': False, 'error': 'No tienes permisos de farmacéutico'}), 401
        
        data = request.get_json() or {}
        pedido_id = data.get('pedido_id')
        
        if not pedido_id:
            return jsonify({'success': False, 'error': 'Falta el ID del pedido'}), 400
            
        # Update order status to CANCELADO
        query = """
            UPDATE pedido
            SET estado = 'CANCELADO', id_farmaceutico_auditor = %s
            WHERE id_pedido = %s
        """
        rows = db.execute_update(query, (session['user_id'], pedido_id))
        
        if rows > 0:
            estructuras.registrar_accion('RECHAZAR_RECETA', 'PEDIDOS', f'Receta rechazada para pedido {pedido_id}')
            return jsonify({'success': True, 'message': 'Receta rechazada con éxito'})
        else:
            return jsonify({'success': False, 'error': 'No se pudo actualizar el pedido'}), 400
    except Exception as e:
        print(f"❌ Error al rechazar receta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pedidos/detalle-admin/<int:pedido_id>')
@login_required
def api_pedido_detalle_admin(pedido_id):
    """API para obtener detalles de un pedido (para admin/farmaceutico)"""
    try:
        if session.get('tipo_usuario') != 'admin':
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
        
        # Obtener información del pedido
        query_pedido = """
            SELECT p.*, c.nombre, c.apellido_paterno, c.ci, c.email, c.telefono
            FROM pedido p
            JOIN cliente c ON p.id_cliente = c.id_cliente
            WHERE p.id_pedido = %s
        """
        pedido = db.execute_query(query_pedido, (pedido_id,))
        
        if not pedido:
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
        
        # Obtener productos del pedido
        query_productos = """
            SELECT dp.*, m.nombre_comercial, m.nombre_generico
            FROM detalle_pedido dp
            JOIN medicamento m ON dp.id_medicamento = m.id_medicamento
            WHERE dp.id_pedido = %s
        """
        productos = db.execute_query(query_productos, (pedido_id,))
        
        return jsonify({
            'success': True,
            'pedido': pedido[0],
            'productos': productos
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/medicamentos/buscar/<nombre>')
@login_required
def api_buscar_medicamento(nombre):
    resultados = estructuras.arbol_medicamentos.buscar_por_prefijo(nombre)
    return jsonify({'resultados': resultados})


@app.route('/api/sucursales/inventario/<int:id_sucursal>')
@login_required
def api_sucursales_inventario(id_sucursal):
    try:
        query = """
            SELECT i.stock_actual AS cantidad, i.stock_minimo, m.nombre_comercial, 'Sección A' AS ubicacion_almacen
            FROM inventario i
            JOIN medicamento m ON i.id_medicamento = m.id_medicamento
            WHERE i.id_sucursal = %s
        """
        inventario = db.execute_query(query, (id_sucursal,)) or []
        return jsonify({'success': True, 'inventario': inventario})
    except Exception as e:
        print(f"❌ Error al obtener inventario de sucursal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sucursales/crear', methods=['POST'])
@login_required
def api_sucursales_crear():
    try:
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        encargado = request.form.get('encargado') or 'Sin encargado'
        ciudad = request.form.get('ciudad') or 'La Paz'
        
        query = """
            INSERT INTO sucursal (nombre, direccion, telefono, encargado, ciudad)
            VALUES (%s, %s, %s, %s, %s)
        """
        id_sucursal = db.execute_insert(query, (nombre, direccion, telefono, encargado, ciudad))
        
        if id_sucursal:
            estructuras.registrar_accion('CREAR_SUCURSAL', 'SUCURSALES', f'Creada sucursal {nombre}')
            return jsonify({'success': True, 'id_sucursal': id_sucursal})
        else:
            return jsonify({'success': False, 'error': 'No se pudo crear la sucursal'}), 500
    except Exception as e:
        print(f"❌ Error al crear sucursal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sucursales/actualizar', methods=['POST'])
@login_required
def api_sucursales_actualizar():
    try:
        id_sucursal = request.form.get('id_sucursal')
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        
        query = """
            UPDATE sucursal 
            SET nombre = %s, direccion = %s, telefono = %s
            WHERE id_sucursal = %s
        """
        db.execute_update(query, (nombre, direccion, telefono, id_sucursal))
        estructuras.registrar_accion('ACTUALIZAR_SUCURSAL', 'SUCURSALES', f'Actualizada sucursal {nombre}')
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Error al actualizar sucursal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sucursales/cambiar-estado', methods=['POST'])
@login_required
def api_sucursales_cambiar_estado():
    try:
        data = request.get_json() or {}
        id_sucursal = data.get('id_sucursal')
        activo = data.get('activo')
        
        estructuras.registrar_accion('CAMBIAR_ESTADO_SUCURSAL', 'SUCURSALES', f'Cambiado estado sucursal {id_sucursal} a {activo}')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/reportes/generar', methods=['GET'])
@login_required
def api_reportes_generar():
    try:
        if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
            
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        tipo = request.args.get('tipo', 'ventas')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({'success': False, 'error': 'Fechas requeridas'}), 400
            
        datos = []
        if tipo == 'ventas':
            query = """
                SELECT s.nombre AS sucursal, DATE_FORMAT(v.fecha, '%Y-%m-%d %H:%i') AS fecha, 
                       COALESCE(CONCAT(c.nombres, ' ', c.apellidos), 'Cliente Casual') AS cliente, 
                       v.total
                FROM venta v
                JOIN sucursal s ON v.id_sucursal = s.id_sucursal
                LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
                WHERE DATE(v.fecha) BETWEEN %s AND %s
                ORDER BY v.fecha DESC
            """
            datos = db.execute_query(query, (fecha_inicio, fecha_fin)) or []
        elif tipo == 'ganancias':
            query = """
                SELECT s.nombre AS sucursal, YEAR(v.fecha) AS anio, MONTH(v.fecha) AS mes, 
                       SUM(v.total) AS total_ventas, ROUND(SUM(v.total) * 0.30, 2) AS ganancia_estimada
                FROM venta v
                JOIN sucursal s ON v.id_sucursal = s.id_sucursal
                WHERE DATE(v.fecha) BETWEEN %s AND %s
                GROUP BY s.nombre, YEAR(v.fecha), MONTH(v.fecha)
                ORDER BY anio DESC, mes DESC
            """
            datos = db.execute_query(query, (fecha_inicio, fecha_fin)) or []
        elif tipo == 'inventario':
            query = """
                SELECT s.nombre AS sucursal, m.nombre_comercial AS medicamento, 
                       i.stock_actual AS stock, i.stock_minimo
                FROM inventario i
                JOIN sucursal s ON i.id_sucursal = s.id_sucursal
                JOIN medicamento m ON i.id_medicamento = m.id_medicamento
                WHERE i.stock_actual <= i.stock_minimo
                ORDER BY s.nombre, m.nombre_comercial
            """
            datos = db.execute_query(query) or []
            
        return jsonify({'success': True, 'datos': datos})
    except Exception as e:
        print(f"Error api_reportes_generar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reportes/exportar/excel', methods=['GET'])
@login_required
def api_reportes_exportar_excel():
    try:
        import csv
        from io import StringIO
        from flask import Response, make_response
        
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        tipo = request.args.get('tipo', 'ventas')
        
        datos = []
        headers = []
        filename = f"reporte_{tipo}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if tipo == 'ventas':
            query = """
                SELECT s.nombre AS sucursal, DATE_FORMAT(v.fecha, '%Y-%m-%d %H:%i') AS fecha, 
                       COALESCE(CONCAT(c.nombres, ' ', c.apellidos), 'Cliente Casual') AS cliente, 
                       v.total AS total_bs
                FROM venta v
                JOIN sucursal s ON v.id_sucursal = s.id_sucursal
                LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
                WHERE DATE(v.fecha) BETWEEN %s AND %s
                ORDER BY v.fecha DESC
            """
            datos = db.execute_query(query, (fecha_inicio, fecha_fin)) or []
            headers = ['SUCURSAL', 'FECHA', 'CLIENTE', 'TOTAL (Bs.)']
        elif tipo == 'ganancias':
            query = """
                SELECT s.nombre AS sucursal, YEAR(v.fecha) AS anio, MONTH(v.fecha) AS mes, 
                       SUM(v.total) AS total_ventas, ROUND(SUM(v.total) * 0.30, 2) AS ganancia_estimada
                FROM venta v
                JOIN sucursal s ON v.id_sucursal = s.id_sucursal
                WHERE DATE(v.fecha) BETWEEN %s AND %s
                GROUP BY s.nombre, YEAR(v.fecha), MONTH(v.fecha)
            """
            datos = db.execute_query(query, (fecha_inicio, fecha_fin)) or []
            headers = ['SUCURSAL', 'ANIO', 'MES', 'TOTAL VENTAS (Bs.)', 'GANANCIA ESTIMADA (Bs.)']
        elif tipo == 'inventario':
            query = """
                SELECT s.nombre AS sucursal, m.nombre_comercial AS medicamento, 
                       i.stock_actual AS stock, i.stock_minimo
                FROM inventario i
                JOIN sucursal s ON i.id_sucursal = s.id_sucursal
                JOIN medicamento m ON i.id_medicamento = m.id_medicamento
                WHERE i.stock_actual <= i.stock_minimo
            """
            datos = db.execute_query(query) or []
            headers = ['SUCURSAL', 'MEDICAMENTO', 'STOCK ACTUAL', 'STOCK MINIMO']
            
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(headers)
        
        for row in datos:
            cw.writerow(list(row.values()))
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename={filename}"
        output.headers["Content-type"] = "text/csv; charset=utf-8"
        return output
    except Exception as e:
        print(f"Error api_reportes_exportar_excel: {e}")
        return redirect(url_for('admin_reportes'))

@app.route('/api/reportes/exportar/pdf', methods=['GET'])
@login_required
def api_reportes_exportar_pdf():
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        tipo = request.args.get('tipo', 'ventas')
        
        datos = []
        if tipo == 'ventas':
            query = """
                SELECT s.nombre AS sucursal, DATE_FORMAT(v.fecha, '%d/%m/%Y %H:%i') AS fecha, 
                       COALESCE(CONCAT(c.nombres, ' ', c.apellidos), 'Cliente Casual') AS cliente, 
                       v.total
                FROM venta v
                JOIN sucursal s ON v.id_sucursal = s.id_sucursal
                LEFT JOIN cliente c ON v.id_cliente = c.id_cliente
                WHERE DATE(v.fecha) BETWEEN %s AND %s
                ORDER BY v.fecha DESC
            """
            datos = db.execute_query(query, (fecha_inicio, fecha_fin)) or []
        elif tipo == 'ganancias':
            query = """
                SELECT s.nombre AS sucursal, CONCAT(MONTH(v.fecha), '/', YEAR(v.fecha)) AS periodo, 
                       SUM(v.total) AS total_ventas, ROUND(SUM(v.total) * 0.30, 2) AS ganancia_estimada
                FROM venta v
                JOIN sucursal s ON v.id_sucursal = s.id_sucursal
                WHERE DATE(v.fecha) BETWEEN %s AND %s
                GROUP BY s.nombre, YEAR(v.fecha), MONTH(v.fecha)
            """
            datos = db.execute_query(query, (fecha_inicio, fecha_fin)) or []
        elif tipo == 'inventario':
            query = """
                SELECT s.nombre AS sucursal, m.nombre_comercial AS medicamento, 
                       i.stock_actual AS stock, i.stock_minimo
                FROM inventario i
                JOIN sucursal s ON i.id_sucursal = s.id_sucursal
                JOIN medicamento m ON i.id_medicamento = m.id_medicamento
                WHERE i.stock_actual <= i.stock_minimo
            """
            datos = db.execute_query(query) or []
            
        return render_template('admin/reporte_pdf.html', datos=datos, tipo=tipo, 
                               fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, hoy=datetime.now().strftime('%d/%m/%Y'))
    except Exception as e:
        print(f"Error api_reportes_exportar_pdf: {e}")
        return redirect(url_for('admin_reportes'))


@app.route('/admin/proveedores')
@login_required
def admin_proveedores():
    if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    query = "SELECT * FROM proveedor ORDER BY razon_social"
    proveedores = db.execute_query(query) or []
    return render_template('admin/proveedores.html', proveedores=proveedores)

@app.route('/api/proveedores/crear', methods=['POST'])
@login_required
def api_proveedores_crear():
    try:
        if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
            
        nit = request.form.get('nit')
        razon_social = request.form.get('razon_social')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        contacto = request.form.get('contacto')
        
        # Check if already exists
        exist_query = "SELECT * FROM proveedor WHERE nit = %s"
        exist = db.execute_query(exist_query, (nit,))
        if exist:
            return jsonify({'success': False, 'error': 'Ya existe un proveedor con ese NIT'}), 400
            
        query = """
            INSERT INTO proveedor (nit, razon_social, direccion, telefono, contacto)
            VALUES (%s, %s, %s, %s, %s)
        """
        id_proveedor = db.execute_insert(query, (nit, razon_social, direccion, telefono, contacto))
        if id_proveedor:
            estructuras.registrar_accion('CREAR_PROVEEDOR', 'PROVEEDORES', f'Creado proveedor {razon_social}')
            return jsonify({'success': True, 'id_proveedor': id_proveedor})
        else:
            return jsonify({'success': False, 'error': 'No se pudo crear el proveedor'}), 500
    except Exception as e:
        print(f"Error api_proveedores_crear: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/proveedores/actualizar', methods=['POST'])
@login_required
def api_proveedores_actualizar():
    try:
        if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
            
        id_proveedor = request.form.get('id_proveedor')
        nit = request.form.get('nit')
        razon_social = request.form.get('razon_social')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        contacto = request.form.get('contacto')
        
        query = """
            UPDATE proveedor
            SET nit = %s, razon_social = %s, direccion = %s, telefono = %s, contacto = %s
            WHERE id_proveedor = %s
        """
        db.execute_update(query, (nit, razon_social, direccion, telefono, contacto, id_proveedor))
        estructuras.registrar_accion('ACTUALIZAR_PROVEEDOR', 'PROVEEDORES', f'Actualizado proveedor {razon_social}')
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error api_proveedores_actualizar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/proveedores/eliminar/<int:id_proveedor>', methods=['POST'])
@login_required
def api_proveedores_eliminar(id_proveedor):
    try:
        if session.get('tipo_usuario') != 'admin' or session.get('rol') != 'ADMIN':
            return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 401
            
        query = "DELETE FROM proveedor WHERE id_proveedor = %s"
        db.execute_delete(query, (id_proveedor,))
        estructuras.registrar_accion('ELIMINAR_PROVEEDOR', 'PROVEEDORES', f'Eliminado proveedor ID {id_proveedor}')
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error api_proveedores_eliminar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ======================================================
# EJECUCIÓN
# ======================================================

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     🏥 FARMACIAS BOLIVIA - SISTEMA DE GESTIÓN INTEGRAL       ║
    ║                                                              ║
    ║     📍 Servidor iniciado en: http://localhost:5000           ║
    ║     🔐 Credenciales por defecto:                             ║
    ║        - ADMIN: ADMIN001 / admin123                          ║
    ║        - FARMACEUTICO: FARM001 / admin123                    ║
    ║        - CAJERO: CAJA001 / admin123                          ║
    ║        - CLIENTE: 123456789 (sin contraseña)                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(debug=True, host='0.0.0.0', port=5000)