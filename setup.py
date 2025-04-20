from setuptools import setup, find_packages

setup(
    name="schwab_trader",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask>=2.3.3",
        "flask-sqlalchemy>=3.1.1",
        "flask-login>=0.6.2",
        "flask-wtf>=1.2.1",
        "flask-migrate>=4.0.5",
        "flask-socketio>=5.5.1",
        "flask-caching>=2.0.2",
        "pytest>=7.4.3",
        "requests>=2.31.0",
        "pandas>=2.1.3",
        "numpy>=1.26.2",
        "python-dotenv>=1.0.0",
        "sqlalchemy>=2.0.23",
        "werkzeug>=2.3.7",
        "jinja2>=3.1.2",
        "alembic>=1.9.0",
        "python-socketio>=5.12.0",
        "cachelib>=0.9.0"
    ],
    python_requires=">=3.6",
) 