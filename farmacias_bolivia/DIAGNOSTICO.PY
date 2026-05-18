# diagnostico.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("DIAGNÓSTICO DEL SISTEMA")
print("=" * 60)

# 1. Verificar conexión a BD
print("\n1. Verificando conexión a MySQL...")
try:
    from utils.conexion import db, test_connection
    if test_connection():
        print("   ✅ Conexión a MySQL OK")
    else:
        print("   ❌ Error de conexión a MySQL")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# 2. Verificar tablas
print("\n2. Verificando tablas...")
query = "SHOW TABLES"
try:
    tablas = db.execute_query(query)
    print(f"   ✅ {len(tablas)} tablas encontradas")
    for t in tablas:
        print(f"      - {list(t.values())[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Verificar usuarios
print("\n3. Verificando usuarios...")
query = "SELECT ci, nombre, rol FROM usuario WHERE activo = TRUE"
try:
    usuarios = db.execute_query(query)
    print(f"   ✅ {len(usuarios) if usuarios else 0} usuarios activos")
    if usuarios:
        for u in usuarios:
            print(f"      - {u['ci']} | {u['nombre']} | {u['rol']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Verificar estructura de datos
print("\n4. Verificando estructuras de datos...")
try:
    from estructura_datos import GestionEstructuras
    estructuras = GestionEstructuras()
    print("   ✅ Estructuras cargadas correctamente")
    print(str(estructuras))
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 60)