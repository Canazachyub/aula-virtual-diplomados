# Aula Virtual

Sistema de gestión de aula virtual con dashboard tipo Padlet con tres tipos de usuarios: Administrador, Docente y Estudiante.

## Características Principales

- **Sistema de Autenticación con 3 Roles:**
  - **Administrador:** Control total del sistema
  - **Docente:** Crear y gestionar cursos, subir materiales
  - **Estudiante:** Inscribirse en cursos y acceder a materiales

- **Dashboard Tipo Padlet:**
  - Organización visual en columnas
  - Tarjetas con diferentes tipos de contenido
  - Soporte para videos, PDFs, imágenes y enlaces

- **Gestión de Materiales:**
  - Subida de archivos multimedia
  - Previsualización integrada
  - Descarga de materiales

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd C:\PROGRAMACION\APPMOBIL\aula-virtual-diplomados
```

### 2. Crear entorno virtual (opcional pero recomendado)

```bash
python -m venv venv

# Activar en Windows:
venv\Scripts\activate

# Activar en Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: http://localhost:5000

## Credenciales por Defecto

- **Usuario Admin:**
  - Usuario: `admin`
  - Contraseña: `admin123`

## Primeros Pasos

1. **Iniciar sesión** con las credenciales de administrador
2. **Crear usuarios** docentes y estudiantes desde el panel de administración
3. **Crear cursos** y asignar docentes
4. **Agregar contenido** usando el dashboard tipo Padlet
5. **Inscribir estudiantes** en los cursos

## Estructura del Proyecto

```
aula-virtual-diplomados/
├── app.py                 # Aplicación Flask principal
├── requirements.txt       # Dependencias Python
├── instance/
│   └── aula_diplomados.db # Base de datos SQLite (se crea automáticamente)
├── static/
│   ├── css/
│   │   └── main.css      # Estilos principales
│   ├── js/
│   │   └── main.js       # JavaScript principal
│   └── uploads/          # Archivos subidos por usuarios
└── templates/
    ├── base.html         # Template base
    ├── index.html        # Página principal
    ├── login.html        # Inicio de sesión
    ├── register.html     # Registro
    ├── dashboard.html    # Dashboard principal
    ├── courses.html      # Lista de cursos
    ├── course_detail.html # Vista del curso con Padlet
    ├── materials.html    # Materiales del curso
    ├── profile.html      # Perfil de usuario
    └── admin/
        ├── dashboard.html    # Panel administrativo
        ├── users.html        # Gestión de usuarios
        └── create_course.html # Crear curso

## Funcionalidades del Dashboard Padlet

### Para Docentes y Administradores:
- Crear columnas personalizadas
- Agregar tarjetas con diferentes tipos de contenido:
  - Texto
  - Enlaces
  - Archivos (PDF, Videos, Imágenes)
- Organizar visualmente el contenido del curso

### Para Estudiantes:
- Ver el contenido organizado en columnas
- Previsualizar videos y PDFs
- Descargar materiales

## Tipos de Archivos Soportados

- **Documentos:** PDF, DOC, DOCX
- **Presentaciones:** PPT, PPTX
- **Videos:** MP4, AVI, MOV
- **Imágenes:** JPG, JPEG, PNG, GIF

## Notas de Desarrollo

- La aplicación usa SQLite como base de datos (ideal para desarrollo)
- Para producción, considerar migrar a PostgreSQL o MySQL
- Los archivos subidos se almacenan en `static/uploads/`
- La aplicación crea automáticamente la base de datos en el primer inicio

## Solución de Problemas

Si encuentras errores al iniciar:

1. Asegúrate de tener Python 3.7+ instalado
2. Verifica que todas las dependencias estén instaladas
3. Elimina la carpeta `instance` para reiniciar la base de datos
4. Revisa que el puerto 5000 no esté en uso

## Próximas Mejoras Sugeridas

- [ ] Implementar notificaciones en tiempo real
- [ ] Agregar sistema de mensajería
- [ ] Implementar evaluaciones y exámenes
- [ ] Agregar generación de certificados
- [ ] Implementar API REST
- [ ] Agregar soporte para videoconferencias
- [ ] Implementar sistema de calificaciones
- [ ] Agregar foro de discusión