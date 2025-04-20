// Main JavaScript file for the index page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Index page loaded');
    // Load API controls
    const apiControlsScript = document.createElement('script');
    apiControlsScript.src = '/static/js/api-controls.js';
    document.head.appendChild(apiControlsScript);
    
    // Add any index page specific functionality here
}); 