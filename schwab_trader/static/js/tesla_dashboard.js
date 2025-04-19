// Initialize chart
let volumeChart = null;

// Function to load volume data based on market condition
async function loadVolumeData(marketCondition) {
    try {
        const response = await fetch(`/dashboard/api/test_data/TSLA/${marketCondition}`);
        if (!response.ok) {
            throw new Error('Failed to fetch volume data');
        }
        
        const data = await response.json();
        if (data.status !== 'success') {
            throw new Error(data.message || 'Error loading data');
        }
        
        // Process the data for the chart
        const chartData = {
            labels: data.data.prices.map(p => p.date),
            datasets: [{
                label: 'Volume',
                data: data.data.prices.map(p => p.volume),
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        };
        
        // Update or create the chart
        if (volumeChart) {
            volumeChart.data = chartData;
            volumeChart.update();
        } else {
            const ctx = document.getElementById('volumeChart').getContext('2d');
            volumeChart = new Chart(ctx, {
                type: 'bar',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Volume'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: `Volume Analysis - ${marketCondition.charAt(0).toUpperCase() + marketCondition.slice(1)} Market`
                        }
                    }
                }
            });
        }
        
        // Update market condition info
        document.getElementById('marketConditionInfo').innerHTML = `
            <p>Period: ${data.data.period.start} to ${data.data.period.end}</p>
            <p>Price Range: $${Math.min(...data.data.prices.map(p => p.low)).toFixed(2)} - $${Math.max(...data.data.prices.map(p => p.high)).toFixed(2)}</p>
        `;
        
    } catch (error) {
        console.error('Error loading volume data:', error);
        showNotification('Error loading volume data: ' + error.message, 'error');
    }
}

// Event listener for market condition selector
document.getElementById('marketCondition').addEventListener('change', (e) => {
    loadVolumeData(e.target.value);
});

// Load initial data
document.addEventListener('DOMContentLoaded', () => {
    loadVolumeData('bullish'); // Default to bullish market
}); 