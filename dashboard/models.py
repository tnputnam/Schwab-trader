from django.db import models
from django.contrib.auth.models import User

class Strategy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Strategies"

class BacktestResult(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    timeframe = models.CharField(max_length=10)
    start_date = models.DateField()
    end_date = models.DateField()
    initial_capital = models.DecimalField(max_digits=12, decimal_places=2)
    total_return = models.DecimalField(max_digits=10, decimal_places=2)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=2)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=2)
    equity_curve = models.JSONField()
    trade_history = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.strategy.name} - {self.symbol} ({self.start_date} to {self.end_date})"

class Portfolio(models.Model):
    symbol = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    avg_cost = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    market_value = models.DecimalField(max_digits=12, decimal_places=2)
    unrealized_pnl = models.DecimalField(max_digits=12, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.quantity} shares"

    class Meta:
        verbose_name_plural = "Portfolio Positions"
