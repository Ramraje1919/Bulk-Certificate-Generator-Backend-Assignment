"""Initial schema for jobs and certificates

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-07 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_name', sa.String(length=255), nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('issued_by', sa.String(length=255), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'PARTIALLY_COMPLETED', 'FAILED', name='jobstatus'), nullable=False),
        sa.Column('total_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_job_name'), 'jobs', ['job_name'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)

    # 2. Create certificates table
    op.create_table(
        'certificates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('certificate_id', sa.String(length=64), nullable=False),
        sa.Column('verification_token', sa.String(length=64), nullable=False),
        sa.Column('recipient_name', sa.String(length=255), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED', name='certificatestatus'), nullable=False),
        sa.Column('pdf_path', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_certificates_job_id'), 'certificates', ['job_id'], unique=False)
    op.create_index(op.f('ix_certificates_certificate_id'), 'certificates', ['certificate_id'], unique=True)
    op.create_index(op.f('ix_certificates_verification_token'), 'certificates', ['verification_token'], unique=True)
    op.create_index(op.f('ix_certificates_recipient_email'), 'certificates', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_certificates_status'), 'certificates', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_certificates_status'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_recipient_email'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_verification_token'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_certificate_id'), table_name='certificates')
    op.drop_index(op.f('ix_certificates_job_id'), table_name='certificates')
    op.drop_table('certificates')
    op.execute('DROP TYPE IF EXISTS certificatestatus;')

    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_job_name'), table_name='jobs')
    op.drop_table('jobs')
    op.execute('DROP TYPE IF EXISTS jobstatus;')
