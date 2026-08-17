"""Add scheduled import sources and run history.

Revision ID: 0002_import_automation
Revises: 0001_domain_core
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_import_automation"
down_revision: str | None = "0001_domain_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid = postgresql.UUID(as_uuid=True)
jsonb = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "import_sources",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("provider_type", sa.String(50), nullable=False),
        sa.Column("endpoint_url", sa.String(1000), nullable=False),
        sa.Column("interval_minutes", sa.Integer, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("configuration", jsonb, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_import_sources_enabled", "import_sources", ["enabled"])
    op.create_index("ix_import_sources_next_run_at", "import_sources", ["next_run_at"])
    op.create_table(
        "import_runs",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "source_id",
            uuid,
            sa.ForeignKey("import_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("RUNNING", "COMPLETED", "PARTIAL", "FAILED", name="import_run_status"),
            nullable=False,
        ),
        sa.Column("trigger", sa.String(30), nullable=False),
        sa.Column("received", sa.Integer, nullable=False),
        sa.Column("created", sa.Integer, nullable=False),
        sa.Column("updated", sa.Integer, nullable=False),
        sa.Column("unchanged", sa.Integer, nullable=False),
        sa.Column("error_count", sa.Integer, nullable=False),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_import_runs_source_id", "import_runs", ["source_id"])


def downgrade() -> None:
    op.drop_table("import_runs")
    op.drop_table("import_sources")
    sa.Enum(name="import_run_status").drop(op.get_bind(), checkfirst=True)
