from schwab_trader import create_app
from schwab_trader.models.user import User, db

def create_test_user():
    """Create a test user for development."""
    app = create_app()
    with app.app_context():
        username = 'test'
        password = 'test123'
        email = 'test@example.com'
        
        if User.query.filter_by(username=username).first():
            print('Test user already exists')
            return
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        print(f'Created test user:\nUsername: {username}\nPassword: {password}\nEmail: {email}')

if __name__ == '__main__':
    create_test_user() 