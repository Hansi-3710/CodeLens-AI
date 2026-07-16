"""add selected_models to experiments

Revision ID: ae21d4edec96
Revises: ea2a1f3bf9c8
Create Date: 2026-07-16 02:45:00.000000

Hand-written for the same reason as ea2a1f3bf9c8: autogenerate against
SQLite (the only dialect available in this environment) also emits
spurious NUMERIC->UUID alter_column ops for every primary/foreign key,
an artifact of SQLite's type reflection. Stripped here — this migration
only adds the one real column.

Backstory: POST /experiments accepted and validated a `models` list but
never persisted it (crud.create_experiment silently discarded it). This
was caught by running the real server end-to-end against a real Postgres
instance and a real LLM provider call — /generate was firing against
every registered model instead of just the ones the user selected. This
column is the fix; see experiments.py's create_experiment and
_run_generation_job for how it's used.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ae21d4edec96'
down_revision = 'ea2a1f3bf9c8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'experiments',
        sa.Column('selected_models', sa.JSON(), nullable=False, server_default='[]'),
    )
    # Drop the server_default after backfilling existing rows — new rows
    # always supply a value explicitly (see database/models.py), so the
    # default was only needed to satisfy NOT NULL on already-existing rows.
    op.alter_column('experiments', 'selected_models', server_default=None)


def downgrade() -> None:
    op.drop_column('experiments', 'selected_models')
