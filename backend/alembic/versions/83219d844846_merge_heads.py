"""merge heads

Revision ID: 83219d844846
Revises: b538a7f0a7a4, a1c3e5f7d9b2
Create Date: 2025-12-16 14:02:02.345311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83219d844846'
down_revision: Union[str, None] = ('b538a7f0a7a4', 'a1c3e5f7d9b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
