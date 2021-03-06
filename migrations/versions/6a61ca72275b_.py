"""empty message

Revision ID: 6a61ca72275b
Revises: 0a75dc478801
Create Date: 2021-02-18 00:25:40.657043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a61ca72275b'
down_revision = '0a75dc478801'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('body_', sa.String(), nullable=True))
    op.drop_column('messages', 'body')
    op.add_column('notifications', sa.Column('body_', sa.String(), nullable=True))
    op.add_column('notifications', sa.Column('header_', sa.String(), nullable=True))
    op.drop_column('notifications', 'body')
    op.drop_column('notifications', 'header')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notifications', sa.Column('header', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('notifications', sa.Column('body', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('notifications', 'header_')
    op.drop_column('notifications', 'body_')
    op.add_column('messages', sa.Column('body', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('messages', 'body_')
    # ### end Alembic commands ###
