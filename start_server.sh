#!/bin/bash
export FLASK_APP=schwab_trader
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONPATH=/home/thomas/Desktop/business/Stock\ Market\ program
flask run --port 5001
