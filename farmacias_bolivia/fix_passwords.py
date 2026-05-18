# fix_all_passwords.py
import bcrypt
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.conexion import db

def fix_user_password(ci, nombre, nueva_password):
    """Actualiza la contraseña de un usuario con un hash bcrypt válido"""
    
    # Generar hash bcrypt válido
    password_hash = bcrypt.hashpw(nueva_password.encode('utf-8'), bcrypt.gensalt())
    hash_str = password_hash.decode('utf-8')
    
    # Actualizar en BD
    query = "UPDATE usuario SET password_hash = %s WHERE ci = %s"
    resultado = db.execute_update(query, (hash_str, ci))
    
    if resultado:
        print(f"✅ {nombre} (CI: {ci}) -> Contraseña: {nueva_password}")
    else:
        print(f"❌ No se encontró usuario con CI: {ci}")
    
    return resultado

if __name__ == "__main__":
    print("=" * 60)
    print("CORRIGIENDO CONTRASEÑAS DE TODOS LOS USUARIOS")
    print("=" * 60)
    print()
    
    # Lista de usuarios con sus contraseñas
    usuarios = [
        {'ci': 'ADMIN001', 'nombre': 'Administrador', 'password': 'admin123'},
        {'ci': 'FARM001', 'nombre': 'Ana Flores', 'password': 'admin123'},
        {'ci': 'FARM002', 'nombre': 'Pedro Torrez', 'password': 'admin123'},
        {'ci': 'CAJA001', 'nombre': 'Laura Quispe', 'password': 'admin123'},
        {'ci': '1234567890', 'nombre': 'Leonardo Admin', 'password': '12345'},
    ]
    
    for user in usuarios:
        fix_user_password(user['ci'], user['nombre'], user['password'])
    
    print("\n" + "=" * 60)
    print("VERIFICANDO TODAS LAS CONTRASEÑAS")
    print("=" * 60)
    
    # Verificar todos los usuarios
    query = "SELECT ci, nombre, password_hash FROM usuario WHERE activo = TRUE"
    usuarios_bd = db.execute_query(query)
    
    for user in usuarios_bd:
        print(f"\n👤 {user['nombre']} (CI: {user['ci']})")
        
        # Determinar qué contraseña probar
        if user['ci'] == '1234567890':
            test_password = '12345'
        else:
            test_password = 'admin123'
        
        try:
            if bcrypt.checkpw(test_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                print(f"   ✅ Contraseña '{test_password}' CORRECTA")
            else:
                print(f"   ❌ Contraseña '{test_password}' INCORRECTA")
        except Exception as e:
            print(f"   ❌ Error: {e}")