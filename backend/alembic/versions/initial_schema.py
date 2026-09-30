"""initial schema

Revision ID: 49a9c8ff6049
Revises: 
Create Date: 2026-09-02 00:41:43.859343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '49a9c8ff6049'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False),
        sa.Column('dealer_name', sa.String(length=100), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )
    op.create_table('projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_name', sa.String(length=100), nullable=False),
        sa.Column('province', sa.String(length=50), nullable=False),
        sa.Column('city', sa.String(length=50), nullable=False),
        sa.Column('product', sa.String(length=100), nullable=False),
        sa.Column('stage', sa.Integer(), nullable=False),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('competitor_info', sa.Text(), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('dealer_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dealer_id'], ['users.id'],),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('decision_makers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('department_name', sa.String(length=100), nullable=False),
        sa.Column('contact_name', sa.String(length=50), nullable=False),
        sa.Column('contact_info', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'],),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('operation_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('operator', sa.String(length=50), nullable=False),
        sa.Column('operation_time', sa.DateTime(), nullable=True),
        sa.Column('field_name', sa.String(length=50), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'],),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('points_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dealer_id', sa.Integer(), nullable=False),
        sa.Column('period', sa.String(length=10), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('points_change', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['dealer_id'], ['users.id'],),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'],),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('token_blacklist',
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('jti'),
    )


def downgrade() -> None:
    op.drop_table('token_blacklist')
    op.drop_table('points_log')
    op.drop_table('operation_logs')
    op.drop_table('decision_makers')
    op.drop_table('projects')
    op.drop_table('users')
