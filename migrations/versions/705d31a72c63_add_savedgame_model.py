"""Add SavedGame model

Revision ID: 705d31a72c63
Revises: 82ba6a0390dd
Create Date: 2024-10-27 15:37:05.406884

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '705d31a72c63'
down_revision = '82ba6a0390dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('saved_game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_name', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.String(length=100), nullable=False),
    sa.Column('save_time', sa.DateTime(), nullable=True),
    sa.Column('conversation_history', sa.Text(), nullable=False),
    sa.Column('storyline', sa.Text(), nullable=False),
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('saved_game')
    # ### end Alembic commands ###
