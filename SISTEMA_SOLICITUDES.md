# Sistema de Solicitudes de Inscripción

## Nuevas Funcionalidades Implementadas

### 🔐 Control de Acceso por Administrador
- Los estudiantes ya no pueden inscribirse directamente a los cursos
- Ahora deben enviar **solicitudes de inscripción** que el admin debe aprobar
- Los docentes también necesitan autorización del admin para acceder a cursos

### 📝 Proceso de Solicitud

#### Para Estudiantes:
1. **Ver Cursos**: Navegar a la lista de cursos disponibles
2. **Solicitar Inscripción**: Click en "Solicitar Inscripción" en lugar de "Inscribirse"
3. **Formulario**: Completar formulario con mensaje opcional para el admin
4. **Esperar Aprobación**: La solicitud queda pendiente hasta que el admin la revise

#### Para Administradores:
1. **Notificaciones**: Reciben notificaciones automáticas de nuevas solicitudes
2. **Panel de Gestión**: Acceso desde Dashboard → "Solicitudes" o menú "Gestión"
3. **Revisar Solicitudes**: Ver información del estudiante y curso
4. **Aprobar/Rechazar**: Con mensaje opcional para el estudiante
5. **Inscripción Automática**: Al aprobar, el estudiante se inscribe automáticamente

### 🔔 Sistema de Notificaciones

#### Notificaciones Automáticas:
- **Para Admins**: Nueva solicitud recibida
- **Para Estudiantes**: Solicitud aprobada/rechazada

#### Tipos de Notificaciones:
- **Info**: Nuevas solicitudes
- **Success**: Solicitudes aprobadas
- **Warning**: Solicitudes rechazadas

### 📊 Panel de Control Admin

#### Dashboard Mejorado:
- **Alertas**: Solicitudes pendientes destacadas
- **Contador**: Badge con número de solicitudes pendientes
- **Acceso Rápido**: Botón directo a gestión de solicitudes

#### Gestión de Solicitudes:
- **Vista de Cards**: Cada solicitud en una tarjeta visual
- **Filtros**: Por estado, estudiante o curso
- **Búsqueda**: En tiempo real
- **Estadísticas**: Contadores por estado
- **Procesamiento**: Modal para aprobar/rechazar con mensaje

### 🎓 Dashboard del Estudiante

#### Nueva Sección:
- **"Mis Solicitudes"**: Vista de todas las solicitudes enviadas
- **Estados Visuales**: Colores para pending/approved/rejected
- **Mensajes del Admin**: Mostrar respuestas del administrador
- **Acceso Directo**: Link al curso cuando es aprobado

## 🚀 Rutas Nuevas

### Estudiantes:
- `GET /course/<id>/enroll` - Formulario de solicitud
- `POST /course/<id>/enroll` - Enviar solicitud

### Administradores:
- `GET /admin/enrollment-requests` - Lista de solicitudes
- `POST /admin/process-request/<id>` - Procesar solicitud

## 🗃️ Nuevos Modelos de Base de Datos

### EnrollmentRequest
- `user_id`: ID del estudiante solicitante
- `course_id`: ID del curso solicitado
- `status`: 'pending', 'approved', 'rejected'
- `message`: Mensaje del estudiante
- `admin_message`: Respuesta del admin
- `requested_at`: Fecha de solicitud
- `processed_at`: Fecha de procesamiento
- `processed_by_id`: ID del admin que procesó

### Notification
- `user_id`: Usuario destinatario
- `title`: Título de la notificación
- `message`: Contenido del mensaje
- `type`: Tipo (info, success, warning, danger)
- `is_read`: Estado de lectura
- `created_at`: Fecha de creación
- `related_id` y `related_type`: Relación con otros objetos

## 💡 Flujo Completo

1. **Estudiante** ve cursos disponibles
2. **Estudiante** hace click en "Solicitar Inscripción"
3. **Estudiante** completa formulario con mensaje
4. **Sistema** crea EnrollmentRequest
5. **Sistema** notifica a todos los administradores
6. **Admin** recibe notificación en dashboard
7. **Admin** revisa solicitud en panel de gestión
8. **Admin** aprueba/rechaza con mensaje opcional
9. **Sistema** crea Enrollment (si se aprueba)
10. **Sistema** notifica al estudiante del resultado
11. **Estudiante** ve resultado en su dashboard
12. **Estudiante** accede al curso (si fue aprobado)

## 🎯 Beneficios

- **Control Total**: Admin decide quién accede a cada curso
- **Comunicación**: Mensajes bidireccionales entre admin y estudiantes
- **Trazabilidad**: Historial completo de solicitudes
- **Experiencia**: UX mejorada con notificaciones y estados claros
- **Escalabilidad**: Sistema preparado para múltiples administradores

## 🔧 Próximas Mejoras Sugeridas

- [ ] Notificaciones por email
- [ ] Panel de notificaciones en tiempo real
- [ ] Límites de estudiantes por curso
- [ ] Prerrequisitos para cursos
- [ ] Inscripción masiva por admin
- [ ] Exportar reportes de solicitudes