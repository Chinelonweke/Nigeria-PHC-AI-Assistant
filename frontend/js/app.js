// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Check authentication
function checkAuth() {
    const user = sessionStorage.getItem('user');
    if (!user && !window.location.pathname.includes('index.html')) {
        window.location.href = 'index.html';
    }
    return user ? JSON.parse(user) : null;
}

// Logout function
function logout() {
    sessionStorage.removeItem('user');
    window.location.href = 'index.html';
}

// API Call Helper
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Format Number
function formatNumber(num) {
    return num.toLocaleString();
}

// Format Date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Show Loading
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    }
}

// Show Error
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="alert alert-error">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }
}

// Update last updated time
function updateLastUpdated() {
    const element = document.getElementById('last-updated');
    if (element) {
        element.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('dashboard.html')) {
        const user = checkAuth();
        if (user) {
            document.getElementById('user-name').textContent = user.username;
        }
    }
});