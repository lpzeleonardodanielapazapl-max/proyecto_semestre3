
import os

class Config:
    # Configuración general
    SECRET_KEY = 'farmacias_bolivia_secret_key_2025'
    DEBUG = True
    
    # Configuración de MySQL
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DATABASE = 'farmacias_bolivia_corregida'
    MYSQL_PORT = 3306
    
    # Configuración de archivos
    UPLOAD_FOLDER = 'static/uploads/recetas'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB máximo
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # Configuración de sesión
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session_files')
    
    # Configuración de la aplicación
    APP_NAME = 'Farmacias Bolivia'
    APP_VERSION = '1.0.0'
    
    # Sucursales (para referencia)
    SUCURSALES = {
        1: 'Yungas',
        2: 'Tembladerani', 
        3: 'Sopocachi',
        4: 'Pasoskanky',
        5: 'Faro'
    }
    
    # Métodos de pago
    METODOS_PAGO = ['EFECTIVO', 'QR', 'TARJETA', 'TRANSFERENCIA']
    
    # Estados de pedido
    ESTADOS_PEDIDO = ['PENDIENTE', 'CONFIRMADO', 'PREPARANDO', 'ENVIADO', 'ENTREGADO', 'CANCELADO']
    
    # IVA
    IVA_PORCENTAJE = 13