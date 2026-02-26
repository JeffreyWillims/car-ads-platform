"""seed_admin

Revision ID: 81ddb16c16f6
Revises: df8fd2068229
Create Date: 2026-02-26 20:39:43.928089+00:00

"""
from typing import Sequence, Union
from passlib.context import CryptContext
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81ddb16c16f6'
down_revision: Union[str, None] = 'df8fd2068229'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def upgrade() -> None:
    hashed_pwd = pwd_context.hash("admin123")
    op.execute(
        f"""
        INSERT INTO users (email, hashed_password) 
        VALUES ('admin@auto.com', '{hashed_pwd}') 
        ON CONFLICT (email) DO NOTHING;
        """
    )

def downgrade() -> None:
    op.execute("DELETE FROM users WHERE email = 'admin@auto.com';")