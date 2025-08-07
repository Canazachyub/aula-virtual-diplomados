// Main JavaScript for Aula Virtual Diplomados

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Auto-cerrar alertas después de 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-info)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Animación de fade-in para elementos
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observar cards para animación
    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });
});

// Función para confirmar acciones
function confirmAction(message) {
    return confirm(message || '¿Estás seguro de realizar esta acción?');
}

// Función para mostrar loading spinner
function showLoading() {
    const loadingHtml = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        </div>
    `;
    return loadingHtml;
}

// Función para manejar errores AJAX
function handleAjaxError(error) {
    console.error('Error:', error);
    let message = 'Ha ocurrido un error. Por favor, intenta nuevamente.';
    
    if (error.responseJSON && error.responseJSON.error) {
        message = error.responseJSON.error;
    }
    
    showNotification(message, 'danger');
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = document.querySelector('.container, .container-fluid');
    if (container) {
        const alertElement = document.createElement('div');
        alertElement.innerHTML = alertHtml;
        container.insertBefore(alertElement.firstChild, container.firstChild);
        
        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            const alert = alertElement.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Función para formatear fechas
function formatDate(dateString) {
    const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
    return new Date(dateString).toLocaleDateString('es-ES', options);
}

// Función para validar formularios
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Función para hacer drag and drop en las tarjetas del Padlet (preparación futura)
function initializeDragAndDrop() {
    const cards = document.querySelectorAll('.padlet-card');
    const columns = document.querySelectorAll('.cards-container');
    
    cards.forEach(card => {
        card.draggable = true;
        
        card.addEventListener('dragstart', (e) => {
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', card.innerHTML);
            card.classList.add('dragging');
        });
        
        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
        });
    });
    
    columns.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            column.classList.add('drag-over');
        });
        
        column.addEventListener('dragleave', () => {
            column.classList.remove('drag-over');
        });
        
        column.addEventListener('drop', (e) => {
            e.preventDefault();
            column.classList.remove('drag-over');
            // Aquí se implementaría la lógica para mover la tarjeta
        });
    });
}

// Función para previsualizar archivos antes de subir
function previewFile(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;
    
    const file = input.files[0];
    if (!file) {
        preview.innerHTML = '';
        return;
    }
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const fileType = file.type;
        
        if (fileType.startsWith('image/')) {
            preview.innerHTML = `<img src="${e.target.result}" class="img-fluid rounded" alt="Preview">`;
        } else if (fileType === 'application/pdf') {
            preview.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-file-earmark-pdf"></i> PDF: ${file.name}
                </div>
            `;
        } else if (fileType.startsWith('video/')) {
            preview.innerHTML = `
                <video controls class="w-100">
                    <source src="${e.target.result}" type="${fileType}">
                </video>
            `;
        } else {
            preview.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-file-earmark"></i> Archivo: ${file.name}
                </div>
            `;
        }
    };
    
    reader.readAsDataURL(file);
}

// Función para copiar texto al portapapeles
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copiado al portapapeles', 'success');
        }).catch(err => {
            console.error('Error al copiar:', err);
        });
    } else {
        // Fallback para navegadores antiguos
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Copiado al portapapeles', 'success');
    }
}

// Función para modo oscuro (preparación futura)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
    
    const icon = document.querySelector('#darkModeToggle i');
    if (icon) {
        icon.className = isDarkMode ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    }
}

// Cargar preferencia de modo oscuro
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// Función para buscar en tiempo real
function setupRealtimeSearch(inputId, itemsSelector, searchAttributes) {
    const searchInput = document.getElementById(inputId);
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const items = document.querySelectorAll(itemsSelector);
        
        items.forEach(item => {
            let shouldShow = false;
            
            searchAttributes.forEach(attr => {
                const value = item.getAttribute(`data-${attr}`);
                if (value && value.toLowerCase().includes(searchTerm)) {
                    shouldShow = true;
                }
            });
            
            item.style.display = shouldShow || !searchTerm ? '' : 'none';
        });
    });
}

// Función para extraer ID de YouTube
function getYouTubeVideoId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

// Función para extraer ID de Google Drive
function getGoogleDriveVideoId(url) {
    const regExp = /\/file\/d\/([a-zA-Z0-9_-]+)/;
    const match = url.match(regExp);
    return match ? match[1] : null;
}

// Función para generar embed de video
function generateVideoEmbed(url) {
    // Detectar YouTube
    const youtubeId = getYouTubeVideoId(url);
    if (youtubeId) {
        return `<div class="video-wrapper">
            <iframe src="https://www.youtube.com/embed/${youtubeId}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
            </iframe>
        </div>`;
    }
    
    // Detectar Google Drive
    const driveId = getGoogleDriveVideoId(url);
    if (driveId) {
        return `<div class="video-wrapper">
            <iframe src="https://drive.google.com/file/d/${driveId}/preview" 
                    frameborder="0" 
                    allow="autoplay">
            </iframe>
        </div>`;
    }
    
    // Si no es reconocido, mostrar como enlace normal
    return `<a href="${url}" target="_blank" class="link-preview">
        <i class="bi bi-link-45deg me-2"></i>
        ${url.length > 50 ? url.substring(0, 50) + '...' : url}
    </a>`;
}

// Exportar funciones para uso global
window.confirmAction = confirmAction;
window.showLoading = showLoading;
window.handleAjaxError = handleAjaxError;
window.showNotification = showNotification;
window.formatDate = formatDate;
window.validateForm = validateForm;
window.previewFile = previewFile;
window.copyToClipboard = copyToClipboard;
window.toggleDarkMode = toggleDarkMode;
window.setupRealtimeSearch = setupRealtimeSearch;
window.generateVideoEmbed = generateVideoEmbed;