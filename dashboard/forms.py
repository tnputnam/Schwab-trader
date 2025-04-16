from django import forms
from django.core.exceptions import ValidationError
from .models import Strategy, Portfolio

class StrategyForm(forms.ModelForm):
    class Meta:
        model = Strategy
        fields = ['name', 'description', 'parameters']
        widgets = {
            'parameters': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_parameters(self):
        parameters = self.cleaned_data['parameters']
        try:
            import json
            if isinstance(parameters, str):
                parameters = json.loads(parameters)
            return parameters
        except json.JSONDecodeError:
            raise ValidationError('Parameters must be valid JSON')

class BacktestForm(forms.Form):
    strategy = forms.ModelChoiceField(
        queryset=Strategy.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    symbol = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    timeframe = forms.ChoiceField(
        choices=[
            ('1d', 'Daily'),
            ('1h', 'Hourly'),
            ('15m', '15 Minutes'),
            ('5m', '5 Minutes'),
            ('1m', '1 Minute')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    initial_capital = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        initial=100000.00,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError('Start date must be before end date')

        return cleaned_data

class PortfolioImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )

class ManualPositionForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['symbol', 'quantity', 'avg_cost', 'current_price']
        widgets = {
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'avg_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        avg_cost = cleaned_data.get('avg_cost')
        current_price = cleaned_data.get('current_price')

        if quantity and avg_cost and current_price:
            cleaned_data['market_value'] = quantity * current_price
            cleaned_data['unrealized_pnl'] = (current_price - avg_cost) * quantity

        return cleaned_data 