// API Control functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize API status
    checkApiStatus();

    // Set up event listeners for API toggle buttons
    document.getElementById('schwab-toggle').addEventListener('click', () => toggleApi('schwab'));
    document.getElementById('alpha-vantage-toggle').addEventListener('click', () => toggleApi('alpha-vantage'));
    document.getElementById('yfinance-toggle').addEventListener('click', () => toggleApi('yfinance'));
});

function updateStatusIndicator(apiName, status) {
    const indicator = document.getElementById(`${apiName}-status`);
    const text = document.getElementById(`${apiName}-status-text`);
    const button = document.getElementById(`${apiName}-toggle`);
    
    // Remove all status classes
    indicator.classList.remove('connected', 'disconnected', 'connecting');
    
    switch(status) {
        case 'connected':
            indicator.classList.add('connected');
            text.textContent = 'Connected';
            button.textContent = 'Disconnect';
            button.classList.remove('btn-primary');
            button.classList.add('btn-danger');
            break;
        case 'disconnected':
            indicator.classList.add('disconnected');
            text.textContent = 'Disconnected';
            button.textContent = 'Connect';
            button.classList.remove('btn-danger');
            button.classList.add('btn-primary');
            break;
        case 'connecting':
            indicator.classList.add('connecting');
            text.textContent = 'Connecting...';
            button.disabled = true;
            break;
        case 'error':
            indicator.classList.add('disconnected');
            text.textContent = 'Error';
            button.textContent = 'Retry';
            button.classList.remove('btn-danger');
            button.classList.add('btn-warning');
            break;
    }
}

async function checkApiStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        updateStatusIndicator('schwab', data.schwab);
        updateStatusIndicator('alpha-vantage', data.alpha_vantage);
        updateStatusIndicator('yfinance', data.yfinance);
    } catch (error) {
        console.error('Error checking API status:', error);
        updateStatusIndicator('schwab', 'error');
        updateStatusIndicator('alpha-vantage', 'error');
        updateStatusIndicator('yfinance', 'error');
    }
}

async function toggleApi(apiName) {
    const button = document.getElementById(`${apiName}-toggle`);
    const currentStatus = document.getElementById(`${apiName}-status-text`).textContent;
    
    try {
        updateStatusIndicator(apiName, 'connecting');
        
        const action = currentStatus === 'Connected' ? 'disconnect' : 'connect';
        const response = await fetch(`/api/${apiName}/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to ${action} ${apiName} API`);
        }
        
        const data = await response.json();
        updateStatusIndicator(apiName, data.status);
    } catch (error) {
        console.error(`Error toggling ${apiName} API:`, error);
        updateStatusIndicator(apiName, 'error');
    }
} 