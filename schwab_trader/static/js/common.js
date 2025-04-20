// API Status
function checkAPIStatus() {
    fetch('/dashboard/api/status')
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
                if (data.status === 'ok') {
                    statusElement.classList.add('connected');
                    statusElement.textContent = 'All Services Connected';
                    
                    // Create detailed status display
                    const servicesStatus = document.createElement('div');
                    servicesStatus.className = 'services-status';
                    servicesStatus.innerHTML = `
                        <div class="service-status">
                            <span class="service-name">Schwab API:</span>
                            <span class="status-indicator ${data.services.schwab_api.status}">${data.services.schwab_api.status}</span>
                        </div>
                        <div class="service-status">
                            <span class="service-name">Alpha Vantage:</span>
                            <span class="status-indicator ${data.services.alpha_vantage.status}">${data.services.alpha_vantage.status}</span>
                        </div>
                        <div class="service-status">
                            <span class="service-name">YFinance:</span>
                            <span class="status-indicator ${data.services.yfinance.status}">${data.services.yfinance.status}</span>
                        </div>
                    `;
                    statusElement.appendChild(servicesStatus);
                } else {
                    statusElement.classList.add('error');
                    statusElement.textContent = 'API Error';
                    showNotification(data.message || 'API Error', 'error');
                }
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

// Bypass Toggle
function setupBypassToggle() {
    const bypassToggle = document.getElementById('bypassToggle');
    if (!bypassToggle) return;

    // Check initial bypass status
    fetch('/auth/bypass')
        .then(response => response.json())
        .then(data => {
            updateBypassStatus(data.bypassed);
        });

    // Add click handler for bypass toggle
    bypassToggle.addEventListener('click', function() {
        const currentStatus = this.querySelector('#bypassStatus').textContent.includes('On');
        fetch('/auth/bypass', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ bypass: !currentStatus })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateBypassStatus(data.bypassed);
                showToast(`Schwab bypass ${data.bypassed ? 'enabled' : 'disabled'}`);
            } else {
                showToast('Error toggling bypass: ' + data.message, 'error');
            }
        })
        .catch(error => {
            showToast('Error toggling bypass', 'error');
        });
    });

    function updateBypassStatus(isBypassed) {
        const statusElement = document.getElementById('bypassStatus');
        const button = document.getElementById('bypassToggle');
        
        if (isBypassed) {
            statusElement.textContent = 'Schwab Bypass: On';
            button.classList.remove('btn-warning');
            button.classList.add('btn-success');
        } else {
            statusElement.textContent = 'Schwab Bypass: Off';
            button.classList.remove('btn-success');
            button.classList.add('btn-warning');
        }
    }
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupTabNavigation();
    setupAutoRefresh();
    setupBypassToggle();
    checkAPIStatus();
    
    // Add event listener for force bypass off button
    const forceBypassOffButton = document.getElementById('forceBypassOff');
    if (forceBypassOffButton) {
        forceBypassOffButton.addEventListener('click', function() {
            fetch('/auth/force_bypass_off', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateBypassStatus(false);
                    showToast('Schwab bypass disabled');
                    // Reload the page after a short delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('Error disabling bypass: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showToast('Error disabling bypass', 'error');
            });
        });
    }
});

// Common JavaScript functions for Schwab Trader

// Format currency values
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

// Format percentage values
function formatPercent(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

// Format date values
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

// Handle form submission with AJAX
function handleFormSubmit(form, successCallback, errorCallback) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                if (successCallback) successCallback(data);
            } else {
                throw new Error(data.message || 'Form submission failed');
            }
        } catch (error) {
            if (errorCallback) errorCallback(error);
            else showAlert(error.message, 'danger');
        }
    });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 