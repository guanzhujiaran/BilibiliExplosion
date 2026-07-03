"""initial migration

Revision ID: 1e997f421d76
Revises: 
Create Date: 2026-07-02 14:35:20.331352

数据库: 请在运行 alembic 时通过 -x db=xxx 指定，version_table 由 env.py 自动管理。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic import context


# revision identifiers, used by Alembic.
revision: str = '1e997f421d76'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (and optionally data)."""
    schema_upgrades()
    if context.get_x_argument(as_dictionary=True).get("data", None):
        data_upgrades()


def downgrade() -> None:
    """Downgrade schema (and optionally data)."""
    if context.get_x_argument(as_dictionary=True).get("data", None):
        data_downgrades()
    schema_downgrades()


def schema_upgrades() -> None:
    """Schema upgrade migrations go here."""
    pass


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    pass


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""
    pass


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
    pass
