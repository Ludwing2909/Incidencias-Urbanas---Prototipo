"""Esquema inicial; snapshot inmutable desde schema_v1.json."""
import json
from pathlib import Path
import sqlalchemy as sa
from alembic import op

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    spec = json.loads((Path(__file__).parents[1] / 'schema_v1.json').read_text(encoding='utf-8'))
    for table in spec:
        columns = []
        for c in table['columns']:
            typ = getattr(sa,c['type'])(c['length']) if c.get('length') else getattr(sa,c['type'])()
            if c['type'] == 'DateTime':
                typ = sa.DateTime(timezone=True)
            fk = [sa.ForeignKey(c['foreign_key'])] if c.get('foreign_key') else []
            columns.append(sa.Column(c['name'],typ,*fk,primary_key=c['pk'],nullable=c['nullable']))
        constraints = [sa.UniqueConstraint(*cols) for cols in table['unique']]
        op.create_table(table['name'],*columns,*constraints)
    op.create_index('ix_incidents_created_at','incidents',['created_at'])
    op.create_index('ix_incidents_state','incidents',['state'])

def downgrade():
    spec = json.loads((Path(__file__).parents[1] / 'schema_v1.json').read_text(encoding='utf-8'))
    for table in reversed(spec):
        op.drop_table(table['name'])
