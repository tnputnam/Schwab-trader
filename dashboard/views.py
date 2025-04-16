from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .models import Strategy, BacktestResult, Portfolio
from .forms import StrategyForm, BacktestForm, PortfolioImportForm, ManualPositionForm
import pandas as pd
import json
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import platform
from django.conf import settings
from django.db import connection
from django.http import HttpResponseServerError
import traceback
import logging

logger = logging.getLogger('dashboard')

@login_required
def index(request):
    """Dashboard home page showing strategies and recent backtests."""
    strategies = Strategy.objects.filter(created_by=request.user)
    recent_backtests = BacktestResult.objects.filter(
        strategy__created_by=request.user
    ).order_by('-created_at')[:5]
    portfolio = Portfolio.objects.all()
    
    portfolio_summary = {
        'total_value': sum(pos.market_value for pos in portfolio),
        'total_pnl': sum(pos.unrealized_pnl for pos in portfolio),
        'position_count': portfolio.count()
    }
    
    return render(request, 'dashboard/index.html', {
        'strategies': strategies,
        'recent_backtests': recent_backtests,
        'portfolio': portfolio,
        'portfolio_summary': portfolio_summary
    })

@login_required
def strategy_list(request):
    """List and create strategies."""
    if request.method == 'POST':
        form = StrategyForm(request.POST)
        if form.is_valid():
            strategy = form.save(commit=False)
            strategy.created_by = request.user
            strategy.save()
            return redirect('strategy_list')
    else:
        form = StrategyForm()
    
    strategies = Strategy.objects.filter(created_by=request.user)
    return render(request, 'dashboard/strategy_list.html', {
        'form': form,
        'strategies': strategies
    })

@login_required
def strategy_detail(request, strategy_id):
    """View and edit strategy details."""
    strategy = get_object_or_404(Strategy, id=strategy_id, created_by=request.user)
    
    if request.method == 'POST':
        form = StrategyForm(request.POST, instance=strategy)
        if form.is_valid():
            form.save()
            return redirect('strategy_list')
    else:
        form = StrategyForm(instance=strategy)
    
    backtests = BacktestResult.objects.filter(strategy=strategy).order_by('-created_at')
    return render(request, 'dashboard/strategy_detail.html', {
        'form': form,
        'strategy': strategy,
        'backtests': backtests
    })

@login_required
def backtest(request):
    """Run strategy backtest."""
    if request.method == 'POST':
        form = BacktestForm(request.POST)
        if form.is_valid():
            try:
                strategy = form.cleaned_data['strategy']
                result = BacktestResult.objects.create(
                    strategy=strategy,
                    symbol=form.cleaned_data['symbol'],
                    timeframe=form.cleaned_data['timeframe'],
                    start_date=form.cleaned_data['start_date'],
                    end_date=form.cleaned_data['end_date'],
                    initial_capital=form.cleaned_data['initial_capital'],
                    total_return=Decimal('0.0'),
                    sharpe_ratio=Decimal('0.0'),
                    max_drawdown=Decimal('0.0'),
                    equity_curve={},
                    trade_history=[]
                )
                # Here you would typically call your backtesting engine
                # For now, we'll just redirect to the results page
                return redirect('backtest_result', backtest_id=result.id)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = BacktestForm()
    
    return render(request, 'dashboard/backtest.html', {'form': form})

@login_required
def backtest_result(request, backtest_id):
    """View backtest results."""
    result = get_object_or_404(BacktestResult, id=backtest_id, strategy__created_by=request.user)
    return render(request, 'dashboard/backtest_result.html', {'result': result})

@login_required
def portfolio_import(request):
    """Import portfolio from Schwab or manual entry."""
    if request.method == 'POST':
        if 'file' in request.FILES:
            form = PortfolioImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    df = pd.read_csv(request.FILES['file'])
                    # Process the CSV file (implementation depends on Schwab's format)
                    return redirect('index')
                except Exception as e:
                    form.add_error('file', str(e))
        else:
            form = ManualPositionForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('index')
    else:
        file_form = PortfolioImportForm()
        position_form = ManualPositionForm()
    
    portfolio = Portfolio.objects.all()
    return render(request, 'dashboard/portfolio_import.html', {
        'file_form': file_form,
        'position_form': position_form,
        'portfolio': portfolio
    })

@require_http_methods(['GET'])
def portfolio_api(request):
    """API endpoint for getting portfolio data."""
    portfolio = Portfolio.objects.all()
    data = [{
        'symbol': p.symbol,
        'quantity': float(p.quantity),
        'avg_cost': float(p.avg_cost),
        'current_price': float(p.current_price),
        'market_value': float(p.market_value),
        'unrealized_pnl': float(p.unrealized_pnl)
    } for p in portfolio]
    
    return JsonResponse({'positions': data})

@require_http_methods(['DELETE'])
def portfolio_position_api(request, symbol):
    """API endpoint for deleting a portfolio position."""
    try:
        position = Portfolio.objects.get(symbol=symbol)
        position.delete()
        return JsonResponse({'success': True})
    except Portfolio.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Position for {symbol} not found'
        })

def debug_view(request):
    """View for displaying system debug information."""
    try:
        # System information
        context = {
            'django_version': f"{django.get_version()}",
            'python_version': f"{sys.version}",
            'os_info': f"{platform.system()} {platform.release()}",
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'installed_apps': settings.INSTALLED_APPS,
            'static_files_ok': True,  # Will be updated below
            'db_connection_ok': True,  # Will be updated below
            'recent_errors': []
        }

        # Check static files configuration
        try:
            from django.contrib.staticfiles.finders import get_finders
            list(get_finders())
        except Exception as e:
            context['static_files_ok'] = False
            logger.error(f"Static files configuration error: {str(e)}")

        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            context['db_connection_ok'] = False
            logger.error(f"Database connection error: {str(e)}")

        # Get recent errors from logs
        try:
            log_file = settings.BASE_DIR / 'logs' / 'errors.log'
            if log_file.exists():
                with open(log_file, 'r') as f:
                    # Get last 10 error lines
                    error_lines = f.readlines()[-10:]
                    context['recent_errors'] = [
                        {
                            'timestamp': line.split(' ')[1] + ' ' + line.split(' ')[2],
                            'type': 'Error',
                            'message': ' '.join(line.split(' ')[3:])
                        }
                        for line in error_lines
                    ]
        except Exception as e:
            logger.error(f"Error reading log file: {str(e)}")

        return render(request, 'debug.html', context)

    except Exception as e:
        logger.error(f"Error in debug view: {str(e)}")
        return HttpResponseServerError(f"Error in debug view: {str(e)}")

def error_handler(request, exception=None):
    """Global error handler that logs errors and redirects to debug view."""
    try:
        # Log the error
        error_info = {
            'timestamp': datetime.now(),
            'type': type(exception).__name__ if exception else 'Unknown',
            'message': str(exception) if exception else 'Unknown error',
            'traceback': traceback.format_exc() if exception else None
        }

        # Log to file
        logger.error(f"Error occurred: {error_info['message']}\nTraceback: {error_info['traceback']}")

        # Redirect to debug view
        from django.shortcuts import redirect
        return redirect('dashboard:debug')
    except Exception as e:
        logger.error(f"Error in error handler: {str(e)}")
        return HttpResponseServerError(f"Error in error handler: {str(e)}")
