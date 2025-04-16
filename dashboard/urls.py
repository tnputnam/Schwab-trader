from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('debug/', views.debug_view, name='debug'),
    path('strategies/', views.strategy_list, name='strategy_list'),
    path('strategies/<int:strategy_id>/', views.strategy_detail, name='strategy_detail'),
    path('backtest/', views.backtest, name='backtest'),
    path('backtest/<int:backtest_id>/', views.backtest_result, name='backtest_result'),
    path('portfolio/import/', views.portfolio_import, name='portfolio_import'),
    path('api/portfolio/', views.portfolio_api, name='portfolio_api'),
    path('api/portfolio/<str:symbol>/', views.portfolio_position_api, name='portfolio_position_api'),
]

# Set up error handlers
handler400 = views.error_handler
handler403 = views.error_handler
handler404 = views.error_handler
handler500 = views.error_handler 