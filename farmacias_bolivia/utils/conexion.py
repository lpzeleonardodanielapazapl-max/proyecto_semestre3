# ======================================================
# CONEXIÓN A LA BASE DE DATOS
# ======================================================

import mysql.connector
from mysql.connector import Error
import sys
import os

# Agregar el directorio padre al path para importar config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa la conexión a la base de datos"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
                port=Config.MYSQL_PORT,
                autocommit=False,
                use_pure=True
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("✅ Conexión a MySQL establecida exitosamente")
        except Error as e:
            print(f"❌ Error al conectar a MySQL: {e}")
            self.connection = None
            self.cursor = None
    
    def get_connection(self):
        """Retorna la conexión activa"""
        if self.connection is None or not self.connection.is_connected():
            self._initialize()
        return self.connection
    
    def get_cursor(self):
        """Retorna el cursor activo"""
        if self.cursor is None:
            self._initialize()
        return self.cursor
    
    def execute_query(self, query, params=None):
        """Ejecuta una consulta y retorna los resultados"""
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Error en consulta: {e}")
            return None
    
    def execute_insert(self, query, params=None):
        """Ejecuta un INSERT y retorna el ID generado"""
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"❌ Error en INSERT: {e}")
            self.connection.rollback()
            return None
    
    def execute_update(self, query, params=None):
        """Ejecuta un UPDATE y retorna el número de filas afectadas"""
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.rowcount
        except Error as e:
            print(f"❌ Error en UPDATE: {e}")
            self.connection.rollback()
            return 0
    
    def execute_delete(self, query, params=None):
        """Ejecuta un DELETE y retorna el número de filas afectadas"""
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.rowcount
        except Error as e:
            print(f"❌ Error en DELETE: {e}")
            self.connection.rollback()
            return 0
    
    def call_procedure(self, procedure_name, params=None):
        """Ejecuta un procedimiento almacenado"""
        try:
            cursor = self.get_cursor()
            cursor.callproc(procedure_name, params or ())
            self.connection.commit()
            return cursor.fetchall()
        except Error as e:
            print(f"❌ Error en procedimiento: {e}")
            self.connection.rollback()
            return None
    
    def close(self):
        """Cierra la conexión"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 Conexión a MySQL cerrada")

# Instancia global de la base de datos
db = Database()

# Función para obtener la conexión fácilmente
def get_db():
    return db

# Función de prueba
def test_connection():
    """Prueba la conexión a la base de datos"""
    result = db.execute_query("SELECT 'Conexión exitosa' as mensaje, DATABASE() as base_datos, NOW() as fecha_hora")
    if result:
        print(f"📊 Base de datos: {result[0]['base_datos']}")
        print(f"📅 Fecha/Hora: {result[0]['fecha_hora']}")
        print(f"✅ {result[0]['mensaje']}")
        return True
    else:
        print("❌ Error en la conexión")
        return False

# Prueba de conexión al importar
if __name__ == "__main__":
    test_connection()