"""Aff fs_uniquifier

Revision ID: 39026e355c0f
Revises: 
Create Date: 2023-05-26 14:29:14.896250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39026e355c0f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('user', sa.Column('fs_uniquifier', sa.String(255), nullable=True))
    op.create_unique_constraint("uq_user_fs_uniquifier", "user", ["fs_uniquifier"])

def downgrade() -> None:
    op.drop_column('user', 'fs_uniquifier')
