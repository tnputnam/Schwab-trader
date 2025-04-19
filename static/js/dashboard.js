// Dashboard JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    // Initialize WebSocket connection
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    // Fetch portfolio data
    async function fetchPortfolioData() {
        try {
            const response = await fetch('/api/portfolio');
            const data = await response.json();
            updatePortfolioSummary(data);
            updateRecentTrades(data.recent_trades);
            updatePortfolioChart(data.history);
        } catch (error) {
            console.error('Error fetching portfolio data:', error);
        }
    }

    // Update portfolio summary
    function updatePortfolioSummary(data) {
        const summaryDiv = document.getElementById('portfolio-summary');
        summaryDiv.innerHTML = `
            <p>Total Value: $${data.total_value.toFixed(2)}</p>
            <p>Cash Balance: $${data.cash_balance.toFixed(2)}</p>
            <h5>Positions:</h5>
            <ul>
                ${data.positions.map(pos => `
                    <li>${pos.symbol}: ${pos.quantity} shares @ $${pos.current_price.toFixed(2)}</li>
                `).join('')}
            </ul>
        `;
    }

    // Update recent trades
    function updateRecentTrades(trades) {
        const tradesDiv = document.getElementById('recent-trades');
        tradesDiv.innerHTML = `
            <ul>
                ${trades.map(trade => `
                    <li>${trade.timestamp}: ${trade.action.toUpperCase()} ${trade.quantity} ${trade.symbol} @ $${trade.price.toFixed(2)}</li>
                `).join('')}
            </ul>
        `;
    }

    // Update portfolio chart
    function updatePortfolioChart(history) {
        const ctx = document.getElementById('portfolio-chart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: history.map(h => h.timestamp),
                datasets: [{
                    label: 'Portfolio Value',
                    data: history.map(h => h.total_value),
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }

    // Initial data fetch
    fetchPortfolioData();

    // Set up WebSocket message handler
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'trade') {
            fetchPortfolioData(); // Refresh data when a trade occurs
        }
    };
}); 