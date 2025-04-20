from setuptools import setup, find_packages

setup(
    name="schwab_trader",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-sqlalchemy",
        "flask-login",
        "flask-wtf",
        "pytest",
        "requests",
        "pandas",
        "numpy",
        "python-dotenv",
    ],
    python_requires=">=3.6",
) 