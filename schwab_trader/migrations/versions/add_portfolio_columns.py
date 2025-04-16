"""add portfolio columns

Revision ID: add_portfolio_columns
Revises: 
Create Date: 2024-04-16 12:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_portfolio_columns'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to portfolios table
    op.add_column('portfolios', sa.Column('total_value', sa.Float(), nullable=True))
    op.add_column('portfolios', sa.Column('cash_value', sa.Float(), nullable=True))
    op.add_column('portfolios', sa.Column('day_change', sa.Float(), nullable=True))
    op.add_column('portfolios', sa.Column('day_change_percent', sa.Float(), nullable=True))
    op.add_column('portfolios', sa.Column('total_gain', sa.Float(), nullable=True))
    op.add_column('portfolios', sa.Column('total_gain_percent', sa.Float(), nullable=True))

def downgrade():
    # Remove the columns
    op.drop_column('portfolios', 'total_value')
    op.drop_column('portfolios', 'cash_value')
    op.drop_column('portfolios', 'day_change')
    op.drop_column('portfolios', 'day_change_percent')
    op.drop_column('portfolios', 'total_gain')
    op.drop_column('portfolios', 'total_gain_percent') 