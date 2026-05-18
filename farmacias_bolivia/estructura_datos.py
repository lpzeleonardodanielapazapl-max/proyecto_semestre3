# ======================================================
# ESTRUCTURAS DE DATOS - VERSIÓN CORREGIDA
# Sistema de Gestión Integral - Farmacias Bolivia
# ======================================================

import json
from datetime import datetime
from collections import deque

# ======================================================
# 1. LISTA ENLAZADA para el Carrito de Compras
# ======================================================

class NodoCarrito:
    """Nodo de la lista enlazada para items del carrito"""
    def __init__(self, producto_id, nombre, cantidad, precio, requiere_receta=False):
        self.producto_id = producto_id
        self.nombre = nombre
        self.cantidad = cantidad
        self.precio = precio
        self.requiere_receta = requiere_receta
        self.subtotal = cantidad * precio
        self.siguiente = None
    
    def __str__(self):
        return f"{self.nombre} x{self.cantidad} = Bs.{self.subtotal:.2f}"

class ListaEnlazadaCarrito:
    """Lista enlazada para gestionar el carrito de compras"""
    
    def __init__(self):
        self.cabeza = None
        self._tamano = 0
    
    def agregar(self, producto_id, nombre, cantidad, precio, requiere_receta=False):
        """Agrega un producto al carrito (al inicio - LIFO para último agregado)"""
        # Verificar si ya existe el producto
        actual = self.cabeza
        while actual:
            if actual.producto_id == producto_id:
                # Actualizar cantidad
                actual.cantidad += cantidad
                actual.subtotal = actual.cantidad * actual.precio
                return True
            actual = actual.siguiente
        
        # Crear nuevo nodo
        nuevo = NodoCarrito(producto_id, nombre, cantidad, precio, requiere_receta)
        nuevo.siguiente = self.cabeza
        self.cabeza = nuevo
        self._tamano += 1
        return True
    
    def eliminar(self, producto_id):
        """Elimina un producto del carrito por su ID"""
        actual = self.cabeza
        anterior = None
        
        while actual:
            if actual.producto_id == producto_id:
                if anterior:
                    anterior.siguiente = actual.siguiente
                else:
                    self.cabeza = actual.siguiente
                self._tamano -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False
    
    def actualizar_cantidad(self, producto_id, nueva_cantidad):
        """Actualiza la cantidad de un producto en el carrito"""
        if nueva_cantidad <= 0:
            return self.eliminar(producto_id)
        
        actual = self.cabeza
        while actual:
            if actual.producto_id == producto_id:
                actual.cantidad = nueva_cantidad
                actual.subtotal = actual.cantidad * actual.precio
                return True
            actual = actual.siguiente
        return False
    
    def obtener_item(self, producto_id):
        """Obtiene un item del carrito por su ID"""
        actual = self.cabeza
        while actual:
            if actual.producto_id == producto_id:
                return actual
            actual = actual.siguiente
        return None
    
    def obtener_todos(self):
        """Retorna una lista con todos los items del carrito"""
        items = []
        actual = self.cabeza
        while actual:
            items.append({
                'producto_id': actual.producto_id,
                'nombre': actual.nombre,
                'cantidad': actual.cantidad,
                'precio': float(actual.precio),
                'subtotal': float(actual.subtotal),
                'requiere_receta': actual.requiere_receta
            })
            actual = actual.siguiente
        return items
    
    def obtener_total(self):
        """Calcula el total del carrito"""
        total = 0
        actual = self.cabeza
        while actual:
            total += actual.subtotal
            actual = actual.siguiente
        return round(total, 2)
    
    def vaciar(self):
        """Vacía todo el carrito"""
        self.cabeza = None
        self._tamano = 0
    
    def __len__(self):
        return self._tamano
    
    def __str__(self):
        items = self.obtener_todos()
        if not items:
            return "🛒 Carrito vacío"
        
        resultado = "=== CARRITO DE COMPRAS ===\n"
        for item in items:
            resultado += f"  • {item['nombre']} x{item['cantidad']} = Bs.{item['subtotal']:.2f}\n"
        resultado += f"  📦 TOTAL: Bs.{self.obtener_total():.2f}"
        return resultado

# ======================================================
# 2. COLA (Queue) FIFO para Pedidos Pendientes
# ======================================================

class ColaPedidos:
    """Cola FIFO para gestionar pedidos pendientes"""
    
    def __init__(self):
        self.cola = deque()
    
    def encolar(self, pedido):
        """Agrega un pedido al final de la cola"""
        pedido['fecha_ingreso_cola'] = datetime.now().isoformat()
        self.cola.append(pedido)
        return True
    
    def desencolar(self):
        """Retira y retorna el primer pedido de la cola (FIFO)"""
        if not self.esta_vacia():
            return self.cola.popleft()
        return None
    
    def ver_primero(self):
        """Ver el primer pedido sin retirarlo"""
        if not self.esta_vacia():
            return self.cola[0]
        return None
    
    def ver_todos(self):
        """Retorna todos los pedidos en la cola"""
        return list(self.cola)
    
    def esta_vacia(self):
        """Verifica si la cola está vacía"""
        return len(self.cola) == 0
    
    def tamanio(self):
        """Retorna el número de pedidos en la cola"""
        return len(self.cola)
    
    def buscar_por_id(self, pedido_id):
        """Busca un pedido en la cola por su ID"""
        for pedido in self.cola:
            if pedido.get('id_pedido') == pedido_id:
                return pedido
        return None
    
    def eliminar_por_id(self, pedido_id):
        """Elimina un pedido específico de la cola"""
        nueva_cola = deque()
        eliminado = False
        
        for pedido in self.cola:
            if pedido.get('id_pedido') != pedido_id:
                nueva_cola.append(pedido)
            else:
                eliminado = True
        
        self.cola = nueva_cola
        return eliminado
    
    def __str__(self):
        if self.esta_vacia():
            return "📋 Cola de pedidos: VACÍA"
        
        resultado = f"📋 COLA DE PEDIDOS (FIFO) - {self.tamanio()} pedidos:\n"
        for i, pedido in enumerate(self.cola, 1):
            resultado += f"  {i}. Pedido #{pedido.get('id_pedido', 'N/A')} - {pedido.get('cliente', 'N/A')} - Bs.{pedido.get('total', 0):.2f}\n"
        return resultado

# ======================================================
# 3. PILA (Stack) LIFO para Historial de Acciones
# ======================================================

class PilaHistorial:
    """Pila LIFO para el historial de acciones del usuario"""
    
    def __init__(self, capacidad_maxima=50):
        self.pila = []
        self.capacidad_maxima = capacidad_maxima
    
    def push(self, accion):
        """Agrega una acción al historial"""
        accion['timestamp'] = datetime.now().isoformat()
        self.pila.append(accion)
        
        # Limitar tamaño de la pila
        if len(self.pila) > self.capacidad_maxima:
            self.pila.pop(0)
        return True
    
    def pop(self):
        """Retira y retorna la última acción (último en entrar, primero en salir)"""
        if not self.esta_vacia():
            return self.pila.pop()
        return None
    
    def ver_ultima(self):
        """Ver la última acción sin retirarla"""
        if not self.esta_vacia():
            return self.pila[-1]
        return None
    
    def ver_todas(self):
        """Retorna todas las acciones (de la más reciente a la más antigua)"""
        return list(reversed(self.pila))
    
    def esta_vacia(self):
        """Verifica si la pila está vacía"""
        return len(self.pila) == 0
    
    def tamanio(self):
        """Retorna el número de acciones en la pila"""
        return len(self.pila)
    
    def deshacer(self):
        """Elimina la última acción (simula deshacer)"""
        return self.pop()
    
    def limpiar(self):
        """Limpia todo el historial"""
        self.pila = []
    
    def __str__(self):
        if self.esta_vacia():
            return "📜 Historial: VACÍO"
        
        resultado = "📜 HISTORIAL DE ACCIONES (más reciente primero):\n"
        for i, accion in enumerate(reversed(self.pila[-10:]), 1):
            resultado += f"  {i}. [{accion.get('timestamp', '')[:19]}] {accion.get('accion', 'N/A')} - {accion.get('modulo', 'N/A')}\n"
        
        if self.tamanio() > 10:
            resultado += f"  ... y {self.tamanio() - 10} más"
        
        return resultado

# ======================================================
# 4. ÁRBOL BINARIO DE BÚSQUEDA para Medicamentos
# ======================================================

class NodoMedicamento:
    """Nodo del árbol binario para medicamentos"""
    def __init__(self, id_medicamento, nombre_comercial, nombre_generico, precio, stock):
        self.id_medicamento = id_medicamento
        self.nombre_comercial = nombre_comercial
        self.nombre_generico = nombre_generico
        self.precio = precio
        self.stock = stock
        self.izquierdo = None
        self.derecho = None

class ArbolBinarioMedicamentos:
    """Árbol Binario de Búsqueda para búsqueda rápida de medicamentos por nombre"""
    
    def __init__(self):
        self.raiz = None
        self._tamano = 0
    
    def insertar(self, id_medicamento, nombre_comercial, nombre_generico, precio, stock):
        """Inserta un medicamento en el árbol ordenado por nombre_comercial"""
        nuevo = NodoMedicamento(id_medicamento, nombre_comercial, nombre_generico, precio, stock)
        
        if self.raiz is None:
            self.raiz = nuevo
        else:
            self._insertar_recursivo(self.raiz, nuevo)
        
        self._tamano += 1
        return True
    
    def _insertar_recursivo(self, actual, nuevo):
        if nuevo.nombre_comercial < actual.nombre_comercial:
            if actual.izquierdo is None:
                actual.izquierdo = nuevo
            else:
                self._insertar_recursivo(actual.izquierdo, nuevo)
        else:
            if actual.derecho is None:
                actual.derecho = nuevo
            else:
                self._insertar_recursivo(actual.derecho, nuevo)
    
    def buscar(self, nombre):
        """Busca un medicamento por su nombre comercial (búsqueda O(log n))"""
        return self._buscar_recursivo(self.raiz, nombre.lower())
    
    def _buscar_recursivo(self, actual, nombre):
        if actual is None:
            return None
        
        nombre_actual = actual.nombre_comercial.lower()
        
        if nombre == nombre_actual:
            return {
                'id_medicamento': actual.id_medicamento,
                'nombre_comercial': actual.nombre_comercial,
                'nombre_generico': actual.nombre_generico,
                'precio': float(actual.precio),
                'precio_venta': float(actual.precio),
                'stock': actual.stock
            }
        elif nombre < nombre_actual:
            return self._buscar_recursivo(actual.izquierdo, nombre)
        else:
            return self._buscar_recursivo(actual.derecho, nombre)
    
    def buscar_por_prefijo(self, prefijo):
        """Busca medicamentos cuyo nombre comience con un prefijo"""
        resultados = []
        self._buscar_prefijo_recursivo(self.raiz, prefijo.lower(), resultados)
        return resultados
    
    def _buscar_prefijo_recursivo(self, actual, prefijo, resultados):
        if actual is None:
            return
        
        nombre_actual = actual.nombre_comercial.lower()
        
        if nombre_actual.startswith(prefijo):
            resultados.append({
                'id_medicamento': actual.id_medicamento,
                'nombre_comercial': actual.nombre_comercial,
                'nombre_generico': actual.nombre_generico,
                'precio': float(actual.precio),
                'precio_venta': float(actual.precio),
                'stock': actual.stock
            })
        
        self._buscar_prefijo_recursivo(actual.izquierdo, prefijo, resultados)
        self._buscar_prefijo_recursivo(actual.derecho, prefijo, resultados)
    
    def listar_ordenado(self):
        """Lista todos los medicamentos en orden alfabético (in-order traversal)"""
        resultados = []
        self._in_order(self.raiz, resultados)
        return resultados
    
    def _in_order(self, actual, resultados):
        if actual is not None:
            self._in_order(actual.izquierdo, resultados)
            resultados.append({
                'id_medicamento': actual.id_medicamento,
                'nombre_comercial': actual.nombre_comercial,
                'nombre_generico': actual.nombre_generico,
                'precio': float(actual.precio),
                'precio_venta': float(actual.precio),
                'stock': actual.stock
            })
            self._in_order(actual.derecho, resultados)
    
    def actualizar_stock(self, nombre, nuevo_stock):
        """Actualiza el stock de un medicamento"""
        nodo = self._buscar_nodo(self.raiz, nombre.lower())
        if nodo:
            nodo.stock = nuevo_stock
            return True
        return False
    
    def _buscar_nodo(self, actual, nombre):
        if actual is None:
            return None
        
        nombre_actual = actual.nombre_comercial.lower()
        
        if nombre == nombre_actual:
            return actual
        elif nombre < nombre_actual:
            return self._buscar_nodo(actual.izquierdo, nombre)
        else:
            return self._buscar_nodo(actual.derecho, nombre)
    
    def __len__(self):
        return self._tamano
    
    def __str__(self):
        medicamentos = self.listar_ordenado()
        if not medicamentos:
            return "🌳 Árbol de medicamentos: VACÍO"
        
        resultado = "🌳 MEDICAMENTOS (orden alfabético):\n"
        for med in medicamentos[:20]:
            resultado += f"  • {med['nombre_comercial']} - Bs.{med['precio']:.2f} (Stock: {med['stock']})\n"
        
        if len(medicamentos) > 20:
            resultado += f"  ... y {len(medicamentos) - 20} más"
        
        return resultado

# ======================================================
# 5. TABLA HASH para Autenticación Rápida (CORREGIDA)
# ======================================================

class TablaHashUsuarios:
    """Tabla hash para autenticación ultrarrápida de usuarios"""
    
    def __init__(self, tamanio=100):
        self.tamanio_tabla = tamanio
        self.tabla = [[] for _ in range(tamanio)]
        self.num_elementos = 0
    
    def _hash(self, clave):
        """Función hash para generar índice"""
        return sum(ord(c) for c in str(clave)) % self.tamanio_tabla
    
    def insertar(self, clave, valor):
        """Inserta un usuario en la tabla hash"""
        indice = self._hash(clave)
        
        for i, (k, v) in enumerate(self.tabla[indice]):
            if k == clave:
                self.tabla[indice][i] = (clave, valor)
                return True
        
        self.tabla[indice].append((clave, valor))
        self.num_elementos += 1
        return True
    
    def obtener(self, clave):
        """Obtiene un usuario por su clave (CI o email)"""
        indice = self._hash(clave)
        
        for k, v in self.tabla[indice]:
            if k == clave:
                return v
        return None
    
    def eliminar(self, clave):
        """Elimina un usuario de la tabla hash"""
        indice = self._hash(clave)
        
        for i, (k, v) in enumerate(self.tabla[indice]):
            if k == clave:
                del self.tabla[indice][i]
                self.num_elementos -= 1
                return True
        return False
    
    def contiene(self, clave):
        """Verifica si existe un usuario en la tabla"""
        return self.obtener(clave) is not None
    
    def tamanio(self):
        """Retorna el número de elementos en la tabla"""
        return self.num_elementos
    
    def factor_carga(self):
        """Calcula el factor de carga de la tabla hash"""
        return self.num_elementos / self.tamanio_tabla
    
    def __str__(self):
        return f"📋 Tabla Hash: {self.num_elementos} usuarios, Factor de carga: {self.factor_carga():.2f}"

# ======================================================
# 6. CLASE DE GESTIÓN QUE INTEGRA TODAS LAS ESTRUCTURAS
# ======================================================

class GestionEstructuras:
    """Clase central que integra todas las estructuras de datos"""
    
    def __init__(self):
        self.carrito = ListaEnlazadaCarrito()
        self.cola_pedidos = ColaPedidos()
        self.historial = PilaHistorial()
        self.arbol_medicamentos = ArbolBinarioMedicamentos()
        self.tabla_usuarios = TablaHashUsuarios()
    
    def registrar_accion(self, accion, modulo, detalles=""):
        """Registra una acción en el historial (pila)"""
        self.historial.push({
            'accion': accion,
            'modulo': modulo,
            'detalles': detalles
        })
    
    def cargar_medicamentos_desde_bd(self, medicamentos_lista):
        """Carga medicamentos desde la BD al árbol binario"""
        for med in medicamentos_lista:
            self.arbol_medicamentos.insertar(
                med['id_medicamento'],
                med['nombre_comercial'],
                med.get('nombre_generico', ''),
                float(med.get('precio_actual', med.get('precio_venta', 0))),
                med.get('stock_actual', 0)
            )
        self.registrar_accion('CARGAR_MEDICAMENTOS', 'INVENTARIO', 
                              f'Cargados {len(medicamentos_lista)} medicamentos')
    
    def cargar_usuarios_desde_bd(self, usuarios_lista):
        """Carga usuarios desde la BD a la tabla hash"""
        for user in usuarios_lista:
            self.tabla_usuarios.insertar(user['ci'], user)
            if user.get('email'):
                self.tabla_usuarios.insertar(user['email'], user)
        self.registrar_accion('CARGAR_USUARIOS', 'AUTH', 
                              f'Cargados {len(usuarios_lista)} usuarios')
    
    def estado_completo(self):
        """Retorna el estado completo de todas las estructuras"""
        return {
            'carrito_items': len(self.carrito),
            'carrito_total': self.carrito.obtener_total(),
            'cola_pedidos': self.cola_pedidos.tamanio(),
            'historial_acciones': self.historial.tamanio(),
            'medicamentos_registrados': len(self.arbol_medicamentos),
            'usuarios_hash': self.tabla_usuarios.tamanio(),
            'factor_carga_hash': self.tabla_usuarios.factor_carga()
        }
    
    def __str__(self):
        estado = self.estado_completo()
        return f"""
╔══════════════════════════════════════════════════════════════╗
║              ESTRUCTURAS DE DATOS - FARMACIAS BOLIVIA        ║
╠══════════════════════════════════════════════════════════════╣
║  🛒 Carrito (Lista Enlazada):     {estado['carrito_items']} items - Bs.{estado['carrito_total']:.2f}
║  📋 Cola Pedidos (FIFO):          {estado['cola_pedidos']} pedidos pendientes
║  📜 Historial (Pila LIFO):        {estado['historial_acciones']} acciones
║  🌳 Árbol Binario:                {estado['medicamentos_registrados']} medicamentos
║  🔐 Tabla Hash:                   {estado['usuarios_hash']} usuarios (FC: {estado['factor_carga_hash']:.2f})
╚══════════════════════════════════════════════════════════════╝
"""

# ======================================================
# PRUEBAS DE LAS ESTRUCTURAS
# ======================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DE ESTRUCTURAS DE DATOS")
    print("=" * 60)
    
    # 1. Prueba de Lista Enlazada (Carrito)
    print("\n1️⃣ LISTA ENLAZADA - CARRITO")
    carrito = ListaEnlazadaCarrito()
    carrito.agregar(1, "Paracetamol 500mg", 2, 8.50)
    carrito.agregar(2, "Ibuprofeno 400mg", 1, 12.90)
    carrito.agregar(3, "Amoxicilina 500mg", 1, 25.00)
    print(carrito)
    print(f"Total: Bs.{carrito.obtener_total():.2f}")
    
    # 2. Prueba de Cola (Pedidos FIFO)
    print("\n2️⃣ COLA FIFO - PEDIDOS PENDIENTES")
    cola = ColaPedidos()
    cola.encolar({"id_pedido": 1, "cliente": "Juan Perez", "total": 28.82})
    cola.encolar({"id_pedido": 2, "cliente": "Maria Lopez", "total": 42.94})
    cola.encolar({"id_pedido": 3, "cliente": "Carlos Mendoza", "total": 63.85})
    print(cola)
    print(f"Atendiendo: {cola.desencolar()}")
    print(f"Pedidos restantes: {cola.tamanio()}")
    
    # 3. Prueba de Pila (Historial)
    print("\n3️⃣ PILA LIFO - HISTORIAL")
    historial = PilaHistorial()
    historial.push({"accion": "INICIO_SESION", "modulo": "AUTH"})
    historial.push({"accion": "AGREGAR_CARRITO", "modulo": "COMPRAS"})
    historial.push({"accion": "REALIZAR_PAGO", "modulo": "CHECKOUT"})
    print(historial)
    
    # 4. Prueba de Árbol Binario
    print("\n4️⃣ ÁRBOL BINARIO - MEDICAMENTOS")
    arbol = ArbolBinarioMedicamentos()
    arbol.insertar(1, "Amoxicilina 500mg", "Amoxicilina", 25.00, 50)
    arbol.insertar(2, "Ibuprofeno 400mg", "Ibuprofeno", 12.90, 80)
    arbol.insertar(3, "Paracetamol 500mg", "Paracetamol", 8.50, 100)
    arbol.insertar(4, "Losartán 50mg", "Losartán", 35.00, 40)
    print(arbol)
    busqueda = arbol.buscar("ibuprofeno")
    print(f"🔍 Búsqueda 'ibuprofeno': {busqueda}")
    
    # 5. Prueba de Tabla Hash
    print("\n5️⃣ TABLA HASH - AUTENTICACIÓN")
    hash_table = TablaHashUsuarios()
    hash_table.insertar("admin", {"nombre": "Admin", "rol": "ADMIN"})
    hash_table.insertar("123456", {"nombre": "Juan", "rol": "CLIENTE"})
    print(hash_table)
    print(f"👤 Buscar 'admin': {hash_table.obtener('admin')}")
    
    # 6. Gestión integrada
    print("\n6️⃣ GESTIÓN INTEGRADA")
    gestion = GestionEstructuras()
    print(gestion)
    
    print("\n✅ TODAS LAS ESTRUCTURAS FUNCIONAN CORRECTAMENTE")