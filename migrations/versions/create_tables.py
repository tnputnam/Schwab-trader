"""Create initial tables

Revision ID: create_tables
Create Date: 2024-04-20 15:20:00.000000
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic
revision = 'create_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(80), unique=True, nullable=False),
        sa.Column('email', sa.String(120), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(128)),
        sa.Column('name', sa.String(100)),
        sa.Column('access_token', sa.String(200)),
        sa.Column('refresh_token', sa.String(200)),
        sa.Column('token_expires_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )

    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('cost_basis', sa.Float, nullable=False),
        sa.Column('sector', sa.String(50)),
        sa.Column('industry', sa.String(50)),
        sa.Column('pe_ratio', sa.Float),
        sa.Column('market_cap', sa.Float),
        sa.Column('dividend_yield', sa.Float),
        sa.Column('eps', sa.Float),
        sa.Column('beta', sa.Float),
        sa.Column('volume', sa.Integer),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id']),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('positions')
    op.drop_table('portfolios')
    op.drop_table('users') 