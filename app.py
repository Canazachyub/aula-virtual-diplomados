from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import requests
import uuid

app = Flask(__name__)

# Configuración para desarrollo y producción
import os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tu-clave-secreta-aqui-cambiar-en-produccion')

# Base de datos: PostgreSQL en producción, SQLite en desarrollo
if os.environ.get('DATABASE_URL'):
    # Producción (Railway, Heroku, etc.)
    database_url = os.environ.get('DATABASE_URL')
    # Corregir formato de URL si es necesario
    if database_url.startswith('postgres//'):
        database_url = database_url.replace('postgres//', 'postgresql://', 1)
    elif database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Desarrollo local
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aula_diplomados.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov', 'doc', 'docx', 'ppt', 'pptx'}

# Configuración de Google Drive
GOOGLE_DRIVE_FOLDER_ID = '1tOVt0hYbHW580M9Tn6Yr4RagWlTzwtN-'  # Tu carpeta de Drive

def convert_drive_url_to_direct(drive_url):
    """Convierte URL de Google Drive a URL de acceso directo"""
    if 'drive.google.com' in drive_url:
        try:
            if '/d/' in drive_url:
                file_id = drive_url.split('/d/')[1].split('/')[0]
            elif 'id=' in drive_url:
                file_id = drive_url.split('id=')[1].split('&')[0]
            else:
                return drive_url
            
            # URL para vista previa
            preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
            # URL para descarga directa
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            return preview_url
        except:
            return drive_url
    return drive_url

def get_drive_file_info(file_id):
    """Obtiene información de un archivo de Google Drive"""
    try:
        # API pública de Google Drive para obtener metadatos
        api_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=name,mimeType,size&key=YOUR_API_KEY"
        # Por ahora retornamos información básica
        return {
            'name': 'Archivo de Drive',
            'size': 'Desconocido',
            'type': 'Archivo'
        }
    except:
        return None

def get_file_type_from_url(url):
    """Determina el tipo de archivo desde una URL"""
    url_lower = url.lower()
    
    if any(ext in url_lower for ext in ['.pdf']):
        return 'pdf'
    elif any(ext in url_lower for ext in ['.mp4', '.avi', '.mov', '.mkv']):
        return 'video' 
    elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        return 'image'
    elif any(ext in url_lower for ext in ['.doc', '.docx']):
        return 'document'
    elif any(ext in url_lower for ext in ['.ppt', '.pptx']):
        return 'presentation'
    else:
        return 'document'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='student')  # admin, teacher, student
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)
    teaching_courses = db.relationship('Course', backref='teacher', lazy=True)
    materials = db.relationship('Material', backref='uploaded_by', lazy=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, archived
    image_url = db.Column(db.String(200))
    
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    columns = db.relationship('BoardColumn', backref='course', lazy=True, cascade='all, delete-orphan')
    materials = db.relationship('Material', backref='course', lazy=True, cascade='all, delete-orphan')

class BoardColumn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    position = db.Column(db.Integer, default=0)
    color = db.Column(db.String(7), default='#f0f0f0')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cards = db.relationship('Card', backref='column', lazy=True, cascade='all, delete-orphan')

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    column_id = db.Column(db.Integer, db.ForeignKey('board_column.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    card_type = db.Column(db.String(20), default='text')  # text, video, pdf, link, image
    file_url = db.Column(db.String(200))
    link_url = db.Column(db.String(200))
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    created_by = db.relationship('User', backref='cards')

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_type = db.Column(db.String(20))  # pdf, video, document, presentation
    file_url = db.Column(db.String(200))
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.Float, default=0.0)

class EnrollmentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    message = db.Column(db.Text)  # Mensaje del solicitante
    whatsapp_number = db.Column(db.String(20))  # Número de WhatsApp
    voucher_file = db.Column(db.String(200))  # Archivo del voucher/comprobante
    admin_message = db.Column(db.Text)  # Mensaje del admin al aprobar/rechazar
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    user = db.relationship('User', foreign_keys=[user_id], backref='enrollment_requests')
    course = db.relationship('Course', backref='enrollment_requests')
    processed_by = db.relationship('User', foreign_keys=[processed_by_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_id = db.Column(db.Integer)  # ID relacionado (ej: enrollment_request_id)
    related_type = db.Column(db.String(50))  # Tipo relacionado (ej: 'enrollment_request')
    
    user = db.relationship('User', backref='notifications')

class ClassSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Lunes, 1=Martes, ..., 5=Sábado
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    class_type = db.Column(db.String(50), default='regular')  # regular, maraton, simulacro
    meeting_link = db.Column(db.String(500))  # Link permanente de Meet/Zoom
    daily_link = db.Column(db.String(500))  # Link específico del día (opcional)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)  # Notas adicionales
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    course = db.relationship('Course', backref='class_schedules')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Función auxiliar para crear notificaciones
def create_notification(user_id, title, message, notification_type='info', related_id=None, related_type=None):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        related_id=related_id,
        related_type=related_type
    )
    db.session.add(notification)
    db.session.commit()
    return notification

# Función auxiliar para notificar a todos los admins
def notify_admins(title, message, notification_type='info', related_id=None, related_type=None):
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        create_notification(admin.id, title, message, notification_type, related_id, related_type)

# Rutas de autenticación
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        role = request.form.get('role', 'student')
        
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registro exitoso. Por favor inicia sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('index'))

# Dashboard principal
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        courses = Course.query.all()
        users = User.query.all()
        
        # Obtener los últimos 5 usuarios y cursos para el dashboard admin
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_courses = Course.query.order_by(Course.created_at.desc()).limit(5).all()
        
        # Obtener solicitudes pendientes y notificaciones
        pending_requests = EnrollmentRequest.query.filter_by(status='pending').all()
        unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
        
        return render_template('admin/dashboard.html', 
                             courses=courses, 
                             users=users,
                             recent_users=recent_users,
                             recent_courses=recent_courses,
                             pending_requests=pending_requests,
                             unread_notifications=unread_notifications)
    elif current_user.role == 'teacher':
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        return render_template('dashboard.html', courses=courses, is_teacher=True)
    else:
        enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
        enrolled_courses = [e.course for e in enrollments]
        
        # Obtener solicitudes del estudiante
        my_requests = EnrollmentRequest.query.filter_by(user_id=current_user.id).all()
        
        return render_template('dashboard.html', 
                             courses=enrolled_courses, 
                             is_teacher=False,
                             my_requests=my_requests)

# Gestión de cursos
@app.route('/courses')
@login_required
def courses():
    all_courses = Course.query.filter_by(status='active').all()
    enrolled_course_ids = []
    
    if current_user.role == 'student':
        enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
        enrolled_course_ids = [e.course_id for e in enrollments]
    
    return render_template('courses.html', courses=all_courses, enrolled_course_ids=enrolled_course_ids)

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Verificar si el usuario tiene acceso al curso
    is_enrolled = False
    is_teacher = False
    
    if current_user.role == 'admin':
        is_enrolled = True
        is_teacher = True
    elif current_user.role == 'teacher' and course.teacher_id == current_user.id:
        is_enrolled = True
        is_teacher = True
    elif current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
        is_enrolled = enrollment is not None
    
    if not is_enrolled and current_user.role != 'admin':
        flash('No tienes acceso a este curso', 'warning')
        return redirect(url_for('courses'))
    
    columns = BoardColumn.query.filter_by(course_id=course_id).order_by(BoardColumn.position).all()
    
    return render_template('course_detail.html', 
                         course=course, 
                         columns=columns,
                         is_teacher=is_teacher)

@app.route('/course/<int:course_id>/enroll', methods=['GET', 'POST'])
@login_required
def enroll_course(course_id):
    if current_user.role != 'student':
        flash('Solo los estudiantes pueden solicitar inscripción en cursos', 'warning')
        return redirect(url_for('courses'))
    
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'GET':
        # Mostrar formulario de solicitud
        return render_template('enroll_request.html', course=course)
    
    # Verificar si ya está inscrito
    existing_enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        flash('Ya estás inscrito en este curso', 'info')
        return redirect(url_for('course_detail', course_id=course_id))
    
    # Verificar si ya tiene una solicitud pendiente
    existing_request = EnrollmentRequest.query.filter_by(
        user_id=current_user.id,
        course_id=course_id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('Ya tienes una solicitud pendiente para este curso', 'info')
        return redirect(url_for('courses'))
    
    # Crear nueva solicitud
    message = request.form.get('message', '')
    whatsapp_number = request.form.get('whatsapp_number', '')
    
    # Manejar la subida del voucher
    voucher_url = None
    if 'voucher' in request.files:
        voucher_file = request.files['voucher']
        if voucher_file.filename != '' and allowed_file(voucher_file.filename):
            filename = secure_filename(voucher_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"voucher_{timestamp}_{filename}"
            
            # Crear carpeta si no existe
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'vouchers')
            os.makedirs(upload_path, exist_ok=True)
            
            filepath = os.path.join(upload_path, filename)
            voucher_file.save(filepath)
            voucher_url = f"/uploads/vouchers/{filename}"
    
    enrollment_request = EnrollmentRequest(
        user_id=current_user.id,
        course_id=course_id,
        message=message,
        whatsapp_number=whatsapp_number,
        voucher_file=voucher_url
    )
    
    db.session.add(enrollment_request)
    db.session.commit()
    
    # Notificar a los administradores
    notify_admins(
        title='Nueva Solicitud de Inscripción',
        message=f'{current_user.full_name or current_user.username} solicita inscribirse en el curso "{course.name}"',
        notification_type='info',
        related_id=enrollment_request.id,
        related_type='enrollment_request'
    )
    
    flash('Solicitud de inscripción enviada. El administrador la revisará pronto.', 'success')
    return redirect(url_for('courses'))

# API para el dashboard tipo Padlet
@app.route('/api/column/create', methods=['POST'])
@login_required
def create_column():
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.json
    course_id = data.get('course_id')
    title = data.get('title')
    color = data.get('color', '#f0f0f0')
    
    course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'teacher' and course.teacher_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
    
    # Obtener la última posición
    last_column = BoardColumn.query.filter_by(course_id=course_id).order_by(BoardColumn.position.desc()).first()
    position = (last_column.position + 1) if last_column else 0
    
    column = BoardColumn(
        course_id=course_id,
        title=title,
        color=color,
        position=position
    )
    
    db.session.add(column)
    db.session.commit()
    
    return jsonify({
        'id': column.id,
        'title': column.title,
        'color': column.color,
        'position': column.position
    })

@app.route('/api/column/<int:column_id>/edit', methods=['POST'])
@login_required
def edit_column(column_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Solo los administradores pueden editar columnas'}), 403
    
    column = BoardColumn.query.get_or_404(column_id)
    course = Course.query.get(column.course_id)
    
    data = request.json
    new_title = data.get('title')
    new_color = data.get('color', column.color)
    
    if not new_title:
        return jsonify({'error': 'El título es requerido'}), 400
    
    column.title = new_title
    column.color = new_color
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Columna actualizada exitosamente',
        'column': {
            'id': column.id,
            'title': column.title,
            'color': column.color
        }
    })

@app.route('/api/column/<int:column_id>/delete', methods=['POST'])
@login_required
def delete_column(column_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Solo los administradores pueden eliminar columnas'}), 403
    
    column = BoardColumn.query.get_or_404(column_id)
    course = Course.query.get(column.course_id)
    
    # Verificar que no sea la última columna
    remaining_columns = BoardColumn.query.filter_by(course_id=column.course_id).count()
    if remaining_columns <= 1:
        return jsonify({'error': 'No se puede eliminar la última columna del curso'}), 400
    
    # Eliminar todas las tarjetas de la columna primero
    Card.query.filter_by(column_id=column_id).delete()
    
    # Eliminar la columna
    db.session.delete(column)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Columna eliminada exitosamente'
    })

@app.route('/api/card/create', methods=['POST'])
@login_required
def create_card():
    if current_user.role == 'student':
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.json
    column_id = data.get('column_id')
    title = data.get('title')
    content = data.get('content', '')
    card_type = data.get('card_type', 'text')
    link_url = data.get('link_url', '')
    
    column = BoardColumn.query.get_or_404(column_id)
    course = Course.query.get(column.course_id)
    
    if current_user.role == 'teacher' and course.teacher_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
    
    # Obtener la última posición
    last_card = Card.query.filter_by(column_id=column_id).order_by(Card.position.desc()).first()
    position = (last_card.position + 1) if last_card else 0
    
    card = Card(
        column_id=column_id,
        title=title,
        content=content,
        card_type=card_type,
        link_url=link_url,
        position=position,
        created_by_id=current_user.id
    )
    
    db.session.add(card)
    db.session.commit()
    
    return jsonify({
        'id': card.id,
        'title': card.title,
        'content': card.content,
        'card_type': card.card_type,
        'link_url': card.link_url,
        'position': card.position
    })

@app.route('/api/card/<int:card_id>/upload', methods=['POST'])
@login_required
def upload_card_file(card_id):
    if current_user.role == 'student':
        return jsonify({'error': 'No autorizado'}), 403
    
    card = Card.query.get_or_404(card_id)
    column = BoardColumn.query.get(card.column_id)
    course = Course.query.get(column.course_id)
    
    if current_user.role == 'teacher' and course.teacher_id != current_user.id:
        return jsonify({'error': 'No autorizado'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Crear carpeta si no existe
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], str(course.id))
        os.makedirs(upload_path, exist_ok=True)
        
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        # Actualizar el card con la URL del archivo
        card.file_url = f"/uploads/{course.id}/{filename}"
        
        # Determinar el tipo de card basado en la extensión
        extension = filename.rsplit('.', 1)[1].lower()
        if extension == 'pdf':
            card.card_type = 'pdf'
        elif extension in ['mp4', 'avi', 'mov']:
            card.card_type = 'video'
        elif extension in ['jpg', 'jpeg', 'png', 'gif']:
            card.card_type = 'image'
        else:
            card.card_type = 'document'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'file_url': card.file_url,
            'card_type': card.card_type
        })
    
    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Gestión de materiales
@app.route('/course/<int:course_id>/materials')
@login_required
def course_materials(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Verificar acceso
    if current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
        if not enrollment:
            flash('No tienes acceso a este curso', 'warning')
            return redirect(url_for('courses'))
    
    materials = Material.query.filter_by(course_id=course_id).order_by(Material.uploaded_at.desc()).all()
    
    # Obtener horarios de clases
    schedules = ClassSchedule.query.filter_by(course_id=course_id, is_active=True).order_by(ClassSchedule.day_of_week, ClassSchedule.start_time).all()
    
    return render_template('materials.html', course=course, materials=materials, schedules=schedules)

@app.route('/course/<int:course_id>/upload_material', methods=['POST'])
@login_required
def upload_material(course_id):
    if current_user.role == 'student':
        flash('No tienes permisos para subir materiales', 'danger')
        return redirect(url_for('course_materials', course_id=course_id))
    
    course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'teacher' and course.teacher_id != current_user.id:
        flash('No puedes subir materiales a este curso', 'danger')
        return redirect(url_for('course_materials', course_id=course_id))
    
    title = request.form.get('title')
    description = request.form.get('description')
    file = request.files.get('file')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Crear carpeta si no existe
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], str(course_id), 'materials')
        os.makedirs(upload_path, exist_ok=True)
        
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        # Determinar el tipo de archivo
        extension = filename.rsplit('.', 1)[1].lower()
        if extension == 'pdf':
            file_type = 'pdf'
        elif extension in ['mp4', 'avi', 'mov']:
            file_type = 'video'
        elif extension in ['doc', 'docx']:
            file_type = 'document'
        elif extension in ['ppt', 'pptx']:
            file_type = 'presentation'
        else:
            file_type = 'other'
        
        material = Material(
            course_id=course_id,
            title=title,
            description=description,
            file_type=file_type,
            file_url=f"/uploads/{course_id}/materials/{filename}",
            uploaded_by_id=current_user.id
        )
        
        db.session.add(material)
        db.session.commit()
        
        flash('Material subido exitosamente', 'success')
    else:
        flash('Error al subir el archivo', 'danger')
    
    return redirect(url_for('course_materials', course_id=course_id))

# Gestión de horarios de clases
@app.route('/course/<int:course_id>/schedules/manage')
@login_required
def manage_schedules(course_id):
    if current_user.role != 'admin':
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('course_materials', course_id=course_id))
    
    course = Course.query.get_or_404(course_id)
    schedules = ClassSchedule.query.filter_by(course_id=course_id).order_by(ClassSchedule.day_of_week, ClassSchedule.start_time).all()
    
    return render_template('admin/manage_schedules.html', course=course, schedules=schedules)

@app.route('/course/<int:course_id>/schedules/create', methods=['POST'])
@login_required
def create_schedule(course_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    course = Course.query.get_or_404(course_id)
    
    day_of_week = int(request.form.get('day_of_week'))
    start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
    class_type = request.form.get('class_type', 'regular')
    meeting_link = request.form.get('meeting_link', '')
    notes = request.form.get('notes', '')
    
    schedule = ClassSchedule(
        course_id=course_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        class_type=class_type,
        meeting_link=meeting_link,
        notes=notes
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    flash('Horario de clase agregado exitosamente', 'success')
    return redirect(url_for('manage_schedules', course_id=course_id))

@app.route('/schedule/<int:schedule_id>/update_daily_link', methods=['POST'])
@login_required
def update_daily_link(schedule_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    daily_link = request.form.get('daily_link', '')
    
    schedule.daily_link = daily_link
    schedule.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Link diario actualizado'})

@app.route('/schedule/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_schedule(schedule_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    
    if request.method == 'GET':
        # Devolver datos del horario para el modal
        return jsonify({
            'id': schedule.id,
            'day_of_week': schedule.day_of_week,
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M'),
            'class_type': schedule.class_type,
            'meeting_link': schedule.meeting_link or '',
            'notes': schedule.notes or ''
        })
    
    # POST - Actualizar horario
    schedule.day_of_week = int(request.form.get('day_of_week'))
    schedule.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    schedule.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
    schedule.class_type = request.form.get('class_type')
    schedule.meeting_link = request.form.get('meeting_link', '')
    schedule.notes = request.form.get('notes', '')
    schedule.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Horario actualizado exitosamente', 'success')
    return redirect(url_for('manage_schedules', course_id=schedule.course_id))

@app.route('/schedule/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    schedule = ClassSchedule.query.get_or_404(schedule_id)
    schedule.is_active = False
    
    db.session.commit()
    
    flash('Horario eliminado exitosamente', 'success')
    return redirect(url_for('manage_schedules', course_id=schedule.course_id))

# Panel de administración
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/enrollment-requests')
@login_required
def admin_enrollment_requests():
    if current_user.role != 'admin':
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('dashboard'))
    
    requests = EnrollmentRequest.query.order_by(EnrollmentRequest.requested_at.desc()).all()
    return render_template('admin/enrollment_requests.html', requests=requests)

@app.route('/admin/process-request/<int:request_id>', methods=['POST'])
@login_required
def process_enrollment_request(request_id):
    if current_user.role != 'admin':
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('dashboard'))
    
    enrollment_request = EnrollmentRequest.query.get_or_404(request_id)
    action = request.form.get('action')
    admin_message = request.form.get('admin_message', '')
    
    if action == 'approve':
        # Verificar si ya está inscrito (por si se aprobó mientras tanto)
        existing_enrollment = Enrollment.query.filter_by(
            user_id=enrollment_request.user_id,
            course_id=enrollment_request.course_id
        ).first()
        
        if not existing_enrollment:
            # Crear la inscripción
            enrollment = Enrollment(
                user_id=enrollment_request.user_id,
                course_id=enrollment_request.course_id
            )
            db.session.add(enrollment)
        
        # Actualizar el estado de la solicitud
        enrollment_request.status = 'approved'
        enrollment_request.admin_message = admin_message
        enrollment_request.processed_at = datetime.utcnow()
        enrollment_request.processed_by_id = current_user.id
        
        # Notificar al estudiante
        create_notification(
            user_id=enrollment_request.user_id,
            title='Solicitud de Inscripción Aprobada',
            message=f'Tu solicitud para el curso "{enrollment_request.course.name}" ha sido aprobada. {admin_message}',
            notification_type='success',
            related_id=enrollment_request.id,
            related_type='enrollment_request'
        )
        
        flash('Solicitud aprobada exitosamente', 'success')
    
    elif action == 'reject':
        enrollment_request.status = 'rejected'
        enrollment_request.admin_message = admin_message
        enrollment_request.processed_at = datetime.utcnow()
        enrollment_request.processed_by_id = current_user.id
        
        # Notificar al estudiante
        create_notification(
            user_id=enrollment_request.user_id,
            title='Solicitud de Inscripción Rechazada',
            message=f'Tu solicitud para el curso "{enrollment_request.course.name}" ha sido rechazada. {admin_message}',
            notification_type='warning',
            related_id=enrollment_request.id,
            related_type='enrollment_request'
        )
        
        flash('Solicitud rechazada', 'info')
    
    db.session.commit()
    return redirect(url_for('admin_enrollment_requests'))

@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        
        # Cambiar contraseña solo si se proporciona
        new_password = request.form.get('password')
        if new_password and new_password.strip():
            user.password_hash = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar usuario. Verifique que no existan duplicados.', 'danger')
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('No tienes permisos de administrador', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # No permitir eliminar al usuario actual
    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta', 'warning')
        return redirect(url_for('admin_users'))
    
    # Eliminar relaciones antes de eliminar usuario
    try:
        # Eliminar inscripciones
        Enrollment.query.filter_by(user_id=user.id).delete()
        # Eliminar solicitudes de inscripción
        EnrollmentRequest.query.filter_by(user_id=user.id).delete()
        # Eliminar notificaciones
        Notification.query.filter_by(user_id=user.id).delete()
        # Eliminar materiales subidos
        Material.query.filter_by(uploaded_by_id=user.id).delete()
        
        # Si es docente, reasignar sus cursos (opcional: se pueden eliminar o reasignar)
        if user.role == 'teacher':
            courses = Course.query.filter_by(teacher_id=user.id).all()
            for course in courses:
                course.teacher_id = None  # O asignar a otro docente
        
        # Eliminar usuario
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Usuario {user.username} eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar usuario', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.role != 'admin':
        flash('Solo los administradores pueden crear cursos', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        teacher_id = request.form.get('teacher_id')
        
        # Solo admin puede asignar docentes
        if not teacher_id:
            teacher_id = None
        
        # Manejar la subida de imagen del curso
        image_url = None
        if 'course_image' in request.files:
            image_file = request.files['course_image']
            if image_file.filename != '' and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"course_{timestamp}_{filename}"
                
                # Crear carpeta si no existe
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'course_images')
                os.makedirs(upload_path, exist_ok=True)
                
                filepath = os.path.join(upload_path, filename)
                image_file.save(filepath)
                image_url = f"/uploads/course_images/{filename}"
        
        course = Course(
            name=name,
            description=description,
            teacher_id=teacher_id,
            image_url=image_url
        )
        
        db.session.add(course)
        db.session.commit()
        
        # Crear columnas predeterminadas para el tablero Padlet
        default_columns = [
            {'title': 'Introducción', 'color': '#e3f2fd'},
            {'title': 'Contenido Principal', 'color': '#f3e5f5'},
            {'title': 'Recursos', 'color': '#e8f5e9'},
            {'title': 'Actividades', 'color': '#fff3e0'}
        ]
        
        for i, col in enumerate(default_columns):
            column = BoardColumn(
                course_id=course.id,
                title=col['title'],
                color=col['color'],
                position=i
            )
            db.session.add(column)
        
        db.session.commit()
        
        flash('Curso creado exitosamente', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
    
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin/create_course.html', teachers=teachers)

@app.route('/admin/assign-teacher/<int:course_id>', methods=['POST'])
@login_required
def assign_teacher(course_id):
    if current_user.role != 'admin':
        flash('Solo los administradores pueden asignar docentes', 'danger')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    teacher_id = request.form.get('teacher_id')
    
    if teacher_id == 'none':
        course.teacher_id = None
        flash(f'Docente removido del curso "{course.name}"', 'info')
    else:
        teacher = User.query.get_or_404(teacher_id)
        if teacher.role != 'teacher':
            flash('El usuario seleccionado no es un docente', 'warning')
            return redirect(url_for('courses'))
        
        course.teacher_id = teacher_id
        flash(f'Docente {teacher.full_name or teacher.username} asignado al curso "{course.name}"', 'success')
    
    db.session.commit()
    return redirect(url_for('courses'))

@app.route('/api/teachers')
@login_required
def api_teachers():
    if current_user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    teachers = User.query.filter_by(role='teacher').all()
    teachers_data = [
        {
            'id': teacher.id,
            'username': teacher.username,
            'full_name': teacher.full_name,
            'email': teacher.email
        }
        for teacher in teachers
    ]
    
    return jsonify(teachers_data)

# Perfil de usuario
@app.route('/profile')
@login_required
def profile():
    enrollments = []
    if current_user.role == 'student':
        enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    
    teaching_courses = []
    if current_user.role == 'teacher':
        teaching_courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    return render_template('profile.html', 
                         enrollments=enrollments,
                         teaching_courses=teaching_courses)

# Función simplificada para inicializar tablas (usada por init_db.py)
def init_db_tables():
    """Inicializa las tablas de la base de datos"""
    # Crear carpeta de uploads si no existe
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    db.create_all()
    print("✅ Tablas de base de datos creadas")

# Función completa de inicialización (para desarrollo local)
def init_db():
    """Inicialización completa con migraciones y usuario admin"""
    init_db_tables()
    
    with app.app_context():
        # Migración: Agregar campos adicionales si no existen (solo SQLite)
        try:
            if not os.environ.get('DATABASE_URL'):
                # Desarrollo - SQLite
                with db.engine.connect() as connection:
                    result = connection.execute(db.text("PRAGMA table_info(enrollment_request)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'whatsapp_number' not in columns:
                        print("Agregando campo whatsapp_number...")
                        connection.execute(db.text("ALTER TABLE enrollment_request ADD COLUMN whatsapp_number VARCHAR(20)"))
                        connection.commit()
                        print("✅ Campo whatsapp_number agregado")
                        
                    if 'voucher_file' not in columns:
                        print("Agregando campo voucher_file...")
                        connection.execute(db.text("ALTER TABLE enrollment_request ADD COLUMN voucher_file VARCHAR(200)"))
                        connection.commit()
                        print("✅ Campo voucher_file agregado")
                        
        except Exception as e:
            print(f"ℹ️ Migración no necesaria: {e}")
        
        # Crear usuario admin por defecto si no existe
        admin = User.query.filter_by(username='Yubert').first()
        if not admin:
            admin = User(
                username='Yubert',
                email='admin@diplomados.com',
                password_hash=generate_password_hash('aulavirtua123'),
                full_name='Yubert Administrador',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado")
        
        print("🎉 Base de datos inicializada correctamente")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)