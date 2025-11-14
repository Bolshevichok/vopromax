"""remove vk and tg user fields, drop admin and holiday_template

Revision ID: 325fceb64c8c
Revises: 86c962b93381
Create Date: 2025-11-14 18:49:25.212211
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "325fceb64c8c"
down_revision: Union[str, None] = "86c962b93381"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("holiday_template")
    op.drop_table("admin")

    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_constraint("telegram_id", type_="unique")
        batch_op.drop_constraint("vk_id", type_="unique")
        batch_op.drop_column("telegram_id")
        batch_op.drop_column("vk_id")
        batch_op.add_column(sa.Column("max_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.create_table(
        "admin",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("surname", sa.Text(), nullable=False),
        sa.Column("last_name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("department", sa.Text(), nullable=False),
        sa.Column(
            "time_created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("time_updated", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "holiday_template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "time_created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("time_updated", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("user") as batch_op:
        batch_op.add_column(sa.Column("telegram_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("vk_id", sa.BigInteger(), nullable=True))
        batch_op.create_unique_constraint("telegram_id", ["telegram_id"])
        batch_op.create_unique_constraint("vk_id", ["vk_id"])
