document.addEventListener('DOMContentLoaded', function () {
    // AC2: Mark touch devices so CSS can hide keyboard shortcut hints
    if (navigator.maxTouchPoints > 0) {
        document.body.classList.add('touch-device');
    }

    // AC6: Show offline banner if already offline on page load
    if (!navigator.onLine) {
        showOfflineBanner();
    }
});

// AC6: Offline indicator banner
function showOfflineBanner() {
    if (document.getElementById('offline-banner')) return;
    var banner = document.createElement('div');
    banner.id = 'offline-banner';
    banner.className = 'alert alert-warning mb-0 rounded-0 text-center';
    banner.setAttribute('role', 'alert');
    banner.textContent = 'You are offline \u2014 changes cannot be saved until your connection is restored.';
    var main = document.querySelector('main');
    if (main) main.insertBefore(banner, main.firstChild);
}

function hideOfflineBanner() {
    var banner = document.getElementById('offline-banner');
    if (banner) banner.remove();
}

window.addEventListener('offline', showOfflineBanner);
window.addEventListener('online', hideOfflineBanner);

/**
 * Get CSRF token from cookies for POST requests.
 */
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
