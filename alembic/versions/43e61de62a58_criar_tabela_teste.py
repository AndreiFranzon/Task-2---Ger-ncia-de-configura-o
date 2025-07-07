"""criar_tabela_teste

Revision ID: 43e61de62a58
Revises: 
Create Date: 2025-07-07 18:50:48.451981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43e61de62a58'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """
    Cria a tabela 'teste' com uma coluna VARCHAR(10).
    """
    op.create_table(
        "teste",
        sa.Column("teste", sa.String(10), nullable=False)
    )

def downgrade() -> None:
    """Downgrade schema."""
    pass
