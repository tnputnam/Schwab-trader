// Trading JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    // Initialize WebSocket connection
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    // Handle trade form submission
    document.getElementById('trade-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const symbol = document.getElementById('symbol').value.toUpperCase();
        const quantity = parseFloat(document.getElementById('quantity').value);
        const action = document.querySelector('input[name="action"]:checked').value;
        
        try {
            const response = await fetch('/api/trade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol,
                    quantity,
                    action
                })
            });
            
            if (!response.ok) {
                throw new Error('Trade execution failed');
            }
            
            // Clear form
            document.getElementById('symbol').value = '';
            document.getElementById('quantity').value = '';
            
            // Show success message
            alert('Trade executed successfully!');
        } catch (error) {
            console.error('Error executing trade:', error);
            alert('Error executing trade: ' + error.message);
        }
    });

    // Fetch and update watchlist
    async function updateWatchlist() {
        try {
            const response = await fetch('/api/watchlist');
            const watchlist = await response.json();
            const watchlistDiv = document.getElementById('watchlist');
            
            watchlistDiv.innerHTML = `
                <ul>
                    ${watchlist.map(item => `
                        <li>${item.symbol}${item.notes ? ` - ${item.notes}` : ''}</li>
                    `).join('')}
                </ul>
            `;
        } catch (error) {
            console.error('Error fetching watchlist:', error);
        }
    }

    // Fetch and update market data
    async function updateMarketData() {
        try {
            const response = await fetch('/api/market-data');
            const marketData = await response.json();
            const marketDataDiv = document.getElementById('market-data');
            
            marketDataDiv.innerHTML = `
                <table class="table">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Price</th>
                            <th>Change</th>
                            <th>Change %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${marketData.map(stock => `
                            <tr>
                                <td>${stock.symbol}</td>
                                <td>$${stock.price.toFixed(2)}</td>
                                <td class="${stock.change >= 0 ? 'text-success' : 'text-danger'}">
                                    ${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}
                                </td>
                                <td class="${stock.change_percent >= 0 ? 'text-success' : 'text-danger'}">
                                    ${stock.change_percent >= 0 ? '+' : ''}${stock.change_percent.toFixed(2)}%
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } catch (error) {
            console.error('Error fetching market data:', error);
        }
    }

    // Initial data fetch
    updateWatchlist();
    updateMarketData();

    // Set up WebSocket message handler
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'quotes') {
            updateMarketData(); // Refresh market data when new quotes arrive
        }
    };
}); 