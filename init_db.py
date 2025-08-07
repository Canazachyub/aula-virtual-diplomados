#!/usr/bin/env python3
"""
Script de inicialización de base de datos para Render
Ejecuta durante el build process para crear tablas
"""
import os
import sys

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔄 Iniciando inicialización de base de datos...")
    
    # Importar la aplicación y función de inicialización
    try:
        from app import app, db, User
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            print("📊 Verificando conexión a PostgreSQL...")
            
            # Mostrar información de la base de datos
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurada')
            print(f"🔗 DATABASE_URL: {os.environ.get('DATABASE_URL', 'No definida')}")
            print(f"🔗 SQLALCHEMY_DATABASE_URI: {db_url}")
            
            if 'postgresql://' in db_url:
                print("✅ Conectando a PostgreSQL en producción")
            else:
                print("🔧 Usando SQLite en desarrollo")
                
            # Probar conexión
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text('SELECT 1'))
                print("✅ Conexión a base de datos exitosa")
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
                raise
            
            print("🏗️ Creando todas las tablas...")
            db.create_all()
            
            # Verificar que las tablas se crearon
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tablas creadas: {tables}")
            
            # Crear usuario admin si no existe
            admin = User.query.filter_by(username='Yubert').first()
            if not admin:
                print("👤 Creando usuario administrador...")
                admin = User(
                    username='Yubert',
                    email='admin@diplomados.com',
                    password_hash=generate_password_hash('aulavirtua123'),
                    full_name='Yubert Administrador',
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuario admin creado: Yubert")
            else:
                print("ℹ️ Usuario admin ya existe")
            
            print("🎉 Inicialización de base de datos completada exitosamente")
            
    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()