import click
from flask.cli import with_appcontext
from schwab_trader.models.user import db, User
from schwab_trader import create_app

def init_db():
    """Initialize the database."""
    app = create_app()
    with app.app_context():
        db.create_all()

@click.command('create-test-user')
def create_test_user():
    """Create a test user for development."""
    app = create_app()
    with app.app_context():
        username = 'test'
        password = 'test123'
        email = 'test@example.com'
        
        if User.query.filter_by(username=username).first():
            click.echo('Test user already exists')
            return
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        click.echo(f'Created test user:\nUsername: {username}\nPassword: {password}\nEmail: {email}') 