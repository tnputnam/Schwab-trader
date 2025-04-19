// Initialize charts
let volumeChart = null;
let priceChart = null;

// Function to load historical data based on stock and market condition
async function loadHistoricalData(symbol, marketCondition) {
    try {
        const response = await fetch(`/dashboard/api/test_data/${symbol}/${marketCondition}`);
        if (!response.ok) {
            throw new Error('Failed to fetch historical data');
        }
        
        const data = await response.json();
        if (data.status !== 'success') {
            throw new Error(data.message || 'Error loading data');
        }
        
        // Process the data for the charts
        const chartData = {
            labels: data.data.prices.map(p => p.date),
            datasets: [{
                label: 'Volume',
                data: data.data.prices.map(p => p.volume),
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                yAxisID: 'y1'
            }, {
                label: 'Price',
                data: data.data.prices.map(p => p.close),
                borderColor: 'rgba(75, 192, 192, 1)',
                yAxisID: 'y'
            }]
        };
        
        // Update or create the volume chart
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
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Price'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Volume'
                            },
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: `${symbol} - ${marketCondition.charAt(0).toUpperCase() + marketCondition.slice(1)} Market Analysis`
                        }
                    }
                }
            });
        }
        
        // Update market condition info
        const minPrice = Math.min(...data.data.prices.map(p => p.low));
        const maxPrice = Math.max(...data.data.prices.map(p => p.high));
        const avgVolume = Math.round(data.data.prices.reduce((sum, p) => sum + p.volume, 0) / data.data.prices.length);
        
        document.getElementById('marketConditionInfo').innerHTML = `
            <div class="market-stats">
                <p><strong>Period:</strong> ${data.data.period.start} to ${data.data.period.end}</p>
                <p><strong>Price Range:</strong> $${minPrice.toFixed(2)} - $${maxPrice.toFixed(2)}</p>
                <p><strong>Average Daily Volume:</strong> ${avgVolume.toLocaleString()}</p>
                <p><strong>Total Trades:</strong> ${data.data.trades.length}</p>
                <p><strong>Buy/Sell Ratio:</strong> ${data.data.trades.filter(t => t.type === 'buy').length}/${data.data.trades.filter(t => t.type === 'sell').length}</p>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading historical data:', error);
        showNotification('Error loading historical data: ' + error.message, 'error');
    }
}

// Event listeners for stock and market condition selectors
document.getElementById('stockSymbol').addEventListener('change', (e) => {
    const marketCondition = document.getElementById('marketCondition').value;
    loadHistoricalData(e.target.value, marketCondition);
});

document.getElementById('marketCondition').addEventListener('change', (e) => {
    const symbol = document.getElementById('stockSymbol').value;
    loadHistoricalData(symbol, e.target.value);
});

// Load initial data
document.addEventListener('DOMContentLoaded', () => {
    const symbol = document.getElementById('stockSymbol').value;
    const marketCondition = document.getElementById('marketCondition').value;
    loadHistoricalData(symbol, marketCondition);
}); 