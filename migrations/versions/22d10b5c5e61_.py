"""empty message

Revision ID: 22d10b5c5e61
Revises: 0fdac83b3358
Create Date: 2021-02-25 20:22:29.563230

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22d10b5c5e61'
down_revision = '0fdac83b3358'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('clients', 'name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('clients', sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
