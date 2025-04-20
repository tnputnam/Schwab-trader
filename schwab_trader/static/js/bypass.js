document.addEventListener('DOMContentLoaded', function() {
    const bypassToggle = document.getElementById('bypassToggle');
    if (!bypassToggle) {
        console.error('Bypass toggle button not found');
        return;
    }

    // Get initial bypass status
    fetch('/auth/bypass', {
        credentials: 'same-origin'  // Include cookies in the request
    })
        .then(response => response.json())
        .then(data => {
            updateButtonState(data.bypassed);
        })
        .catch(error => {
            console.error('Error fetching bypass status:', error);
            bypassToggle.disabled = true;
        });

    // Handle toggle click
    bypassToggle.addEventListener('click', function() {
        const isEnabled = bypassToggle.classList.contains('btn-warning');
        
        fetch('/auth/bypass', {
            method: 'POST',
            credentials: 'same-origin',  // Include cookies in the request
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ bypass: !isEnabled })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateButtonState(data.bypassed);
                if (data.bypassed && data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            } else {
                console.error('Error:', data.message);
                // Revert button state on error
                updateButtonState(isEnabled);
            }
        })
        .catch(error => {
            console.error('Error toggling bypass:', error);
            // Revert button state on error
            updateButtonState(isEnabled);
        });
    });

    function updateButtonState(enabled) {
        bypassToggle.classList.toggle('btn-warning', enabled);
        bypassToggle.classList.toggle('btn-secondary', !enabled);
        bypassToggle.textContent = `Schwab Bypass: ${enabled ? 'On' : 'Off'}`;
    }
}); 