"""Agrego campos service_order, centro_costo, tipo_servicio y linea

Revision ID: 6b2fc563d750
Revises: 
Create Date: 2025-05-16 13:43:00.285563

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b2fc563d750'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('registros', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contrato', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('service_order', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('centro_costo', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('tipo_servicio', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('linea', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('registros', schema=None) as batch_op:
        batch_op.drop_column('linea')
        batch_op.drop_column('tipo_servicio')
        batch_op.drop_column('centro_costo')
        batch_op.drop_column('service_order')
        batch_op.drop_column('contrato')

    # ### end Alembic commands ###
