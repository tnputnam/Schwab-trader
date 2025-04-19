// API Status
function checkAPIStatus() {
    fetch('/api/status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('API Status:', data);
            const statusElement = document.getElementById('api-status');
            if (statusElement) {
                statusElement.classList.add('connected');
                statusElement.textContent = 'API Connected';
            }
        })
        .catch(error => {
            console.error('Error checking API status:', error);
            const statusElement = document.getElementById('api-status');
            if (statusElement) {
                statusElement.classList.add('error');
                statusElement.textContent = 'API Error';
            }
            showNotification('Unable to connect to API. Please check if the server is running.', 'error');
        });
}

// Tab Navigation
function setupTabNavigation() {
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');
        });
    });
}

// Chart Configuration
function createChartConfig(type, data, options = {}) {
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            }
        },
        scales: {
            y: {
                beginAtZero: false
            }
        }
    };

    return {
        type: type,
        data: data,
        options: { ...defaultOptions, ...options }
    };
}

// Number Formatting
function formatNumber(num) {
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(1) + 'B';
    }
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Stock Actions
function addToWatchlist(symbol) {
    fetch('/api/watchlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ symbol: symbol })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Added to watchlist');
        } else {
            showToast('Error: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Error adding to watchlist', 'error');
    });
}

function setAlert(symbol) {
    const price = prompt('Enter alert price:');
    if (price) {
        fetch('/api/alerts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ symbol: symbol, price: parseFloat(price) })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Alert set successfully');
            } else {
                showToast('Error: ' + data.message, 'error');
            }
        })
        .catch(error => {
            showToast('Error setting alert', 'error');
        });
    }
}

function viewDetails(symbol) {
    window.location.href = `/stock/${symbol}`;
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            ${message}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Auto-refresh
function setupAutoRefresh(interval = 300000) { // 5 minutes default
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            window.location.reload();
        }
    }, interval);
}

// Add notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', () => {
    checkAPIStatus();
    setupTabNavigation();
    setupAutoRefresh();
}); 