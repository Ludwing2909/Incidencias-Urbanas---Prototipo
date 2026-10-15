"""Historial independiente de aclaraciones y decisiones de relación."""
import sqlalchemy as sa
from alembic import op

revision='0002'
down_revision='0001'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('analysis_versions',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('incident_id',sa.String(36),sa.ForeignKey('incidents.id'),nullable=False),
        sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('version',sa.Integer(),nullable=False),
        sa.Column('original_text',sa.Text(),nullable=False),
        sa.Column('answers',sa.JSON(),nullable=False),sa.Column('analysis',sa.JSON(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('incident_id','version'))
    op.create_table('relation_decisions',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('incident_id',sa.String(36),sa.ForeignKey('incidents.id'),nullable=False),
        sa.Column('related_id',sa.String(36),sa.ForeignKey('incidents.id'),nullable=False),
        sa.Column('user_id',sa.String(36),sa.ForeignKey('users.id'),nullable=False),
        sa.Column('decision',sa.String(20),nullable=False),sa.Column('reason',sa.Text(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))

def downgrade():
    op.drop_table('relation_decisions')
    op.drop_table('analysis_versions')
