"""initial migration

Revision ID: 3d3bedcf112d
Revises: 
Create Date: 2026-06-29 15:53:38.272813

数据库: 请在运行 alembic 时通过 -x db=xxx 指定，version_table 由 env.py 自动管理。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d3bedcf112d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
