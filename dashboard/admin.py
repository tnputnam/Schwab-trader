from django.contrib import admin
from .models import Strategy, BacktestResult, Portfolio

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'updated_at')
    list_filter = ('created_by', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):
    list_display = ('strategy', 'symbol', 'timeframe', 'start_date', 'end_date', 'total_return', 'sharpe_ratio')
    list_filter = ('strategy', 'symbol', 'timeframe', 'start_date')
    search_fields = ('strategy__name', 'symbol')
    readonly_fields = ('created_at',)

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'quantity', 'avg_cost', 'current_price', 'market_value', 'unrealized_pnl', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('symbol',)
    readonly_fields = ('last_updated',)
