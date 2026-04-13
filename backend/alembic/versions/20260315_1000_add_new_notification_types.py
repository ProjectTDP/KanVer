"""Add new notification types to check constraint

Revision ID: 20260315_1000
Revises: d4b6a8f2c901
Create Date: 2026-03-15 10:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260315_1000'
down_revision = 'd4b6a8f2c901'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 3 new notification types to the check constraint."""
    # Eski constraint'i sil
    op.drop_constraint('check_notification_type_valid', 'notifications', type_='check')

    # Yeni constraint'i oluştur (3 yeni tip: DONOR_ARRIVED, REQUEST_FULFILLED, REDIRECT_TO_BANK)
    op.create_check_constraint(
        'check_notification_type_valid',
        'notifications',
        "notification_type IN ('NEW_REQUEST', 'DONOR_FOUND', 'DONOR_ON_WAY', 'DONOR_ARRIVED', 'DONATION_COMPLETE', 'REQUEST_FULFILLED', 'TIMEOUT_WARNING', 'NO_SHOW', 'REDIRECT_TO_BANK')"
    )


def downgrade() -> None:
    """Revert to old notification types constraint."""
    # Yeni constraint'i sil
    op.drop_constraint('check_notification_type_valid', 'notifications', type_='check')

    # Eski constraint'i geri yükle
    op.create_check_constraint(
        'check_notification_type_valid',
        'notifications',
        "notification_type IN ('NEW_REQUEST', 'DONOR_FOUND', 'DONOR_ON_WAY', 'DONATION_COMPLETE', 'TIMEOUT_WARNING', 'NO_SHOW')"
    )