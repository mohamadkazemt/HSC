// Initialize Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Handle confirmation prompts
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-danger') || e.target.classList.contains('btn-warning')) {
        if (!confirm('آیا از انجام این عملیات اطمینان دارید؟')) {
            e.preventDefault();
        }
    }
});

// Handle dynamic form validation
document.addEventListener('submit', function(e) {
    if (e.target.classList.contains('needs-validation')) {
        if (!e.target.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        e.target.classList.add('was-validated');
    }
});

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Handle notification marking as read
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('mark-read')) {
        e.preventDefault();
        var notificationId = e.target.dataset.notificationId;
        fetch('/fire-extinguisher-management/notifications/' + notificationId + '/mark-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                e.target.closest('.notification-item').classList.add('read');
                e.target.remove();
            }
        });
    }
});

// Handle mark all as read
document.addEventListener('click', function(e) {
    if (e.target.id === 'mark-all-read') {
        e.preventDefault();
        fetch('/fire-extinguisher-management/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.querySelectorAll('.notification-item').forEach(function(item) {
                    item.classList.add('read');
                });
                document.querySelectorAll('.mark-read').forEach(function(button) {
                    button.remove();
                });
            }
        });
    }
});

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Handle dynamic form fields
document.addEventListener('change', function(e) {
    // Handle location type change
    if (e.target.id === 'id_location_type') {
        const sectionField = document.querySelector('.location-section-field');
        const machineField = document.querySelector('.location-machine-field');
        
        if (e.target.value === 'section') {
            sectionField.style.display = 'block';
            machineField.style.display = 'none';
            document.getElementById('id_location_machine').value = '';
        } else if (e.target.value === 'machine') {
            sectionField.style.display = 'none';
            machineField.style.display = 'block';
            document.getElementById('id_location_section').value = '';
        }
    }
}); 