# ======================================================
# EJECUTAR LA APLICACIÓN
# ======================================================

from app import app

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
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(debug=True, host='0.0.0.0', port=5000)