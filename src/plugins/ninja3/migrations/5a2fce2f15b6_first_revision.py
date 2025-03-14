"""first revision

迁移 ID: 5a2fce2f15b6
父迁移: 
创建时间: 2024-12-10 22:45:45.824631

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '5a2fce2f15b6'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = ('ninja3',)
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ninja3_gameids',
    sa.Column('game_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('game_id', name=op.f('pk_ninja3_gameids')),
    info={'bind_key': 'ninja3'}
    )
    op.create_table('ninja3_giftcodes',
    sa.Column('code', sa.String(length=255), nullable=False),
    sa.Column('time', sa.Date(), nullable=False),
    sa.Column('available', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('code', name=op.f('pk_ninja3_giftcodes')),
    info={'bind_key': 'ninja3'}
    )
    op.create_table('ninja3_users',
    sa.Column('user_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('uid_nums', sa.Integer(), nullable=False),
    sa.Column('need_remind', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_ninja3_users')),
    info={'bind_key': 'ninja3'}
    )
    # ### end Alembic commands ###


def downgrade(name: str = "") -> None:
    if name:
        return
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ninja3_users')
    op.drop_table('ninja3_giftcodes')
    op.drop_table('ninja3_gameids')
    # ### end Alembic commands ###
