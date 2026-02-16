"""Fix roadmap compliance - QR codes, donations, notifications

Revision ID: 002
Revises: 001
Create Date: 2024-02-16 10:00:00.000000

This migration brings the database schema into 100% compliance with the roadmap:
- QR Code model: Rename qr_code_string -> token, add signature and used_by fields
- Donation model: Add donation_type and qr_id fields, rename hero_points_awarded -> hero_points_earned, donated_at -> donation_date
- Notification model: Rename body -> message, replace status enum with is_read and is_push_sent boolean fields
- DonationStatus enum: Replace PENDING/VERIFIED with COMPLETED/CANCELLED
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== QR Codes Table Changes ==========
    # Rename qr_code_string to token
    op.alter_column('qr_codes', 'qr_code_string', new_column_name='token')
    
    # Add signature column
    op.add_column('qr_codes', sa.Column('signature', sa.Text(), nullable=True))
    
    # Add used_by column
    op.add_column('qr_codes', sa.Column('used_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_qr_codes_used_by', 'qr_codes', 'users', ['used_by'], ['user_id'])
    
    # Update indexes
    op.drop_index('idx_qr_codes_string', table_name='qr_codes')
    op.create_index('idx_qr_codes_token', 'qr_codes', ['token'], unique=False)
    op.drop_index('idx_qr_codes_expires', table_name='qr_codes')
    op.create_index('idx_qr_codes_commitment', 'qr_codes', ['commitment_id'], 
                    unique=False, postgresql_where=sa.text('is_used = false'))
    
    # Backfill signature with placeholder (will be regenerated when QR codes are created)
    op.execute("UPDATE qr_codes SET signature = 'legacy' WHERE signature IS NULL")
    op.alter_column('qr_codes', 'signature', nullable=False)
    
    # ========== Donations Table Changes ==========
    # Add donation_type column
    op.add_column('donations', sa.Column('donation_type', sa.String(50), nullable=True))
    
    # Add qr_id column
    op.add_column('donations', sa.Column('qr_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_donations_qr_id', 'donations', 'qr_codes', ['qr_id'], ['qr_id'])
    
    # Rename hero_points_awarded to hero_points_earned
    op.alter_column('donations', 'hero_points_awarded', new_column_name='hero_points_earned')
    
    # Rename donated_at to donation_date
    op.alter_column('donations', 'donated_at', new_column_name='donation_date')
    
    # Add created_at column
    op.add_column('donations', sa.Column('created_at', sa.DateTime(timezone=True), 
                                         nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Remove verified_at and notes columns (not in roadmap)
    op.drop_column('donations', 'verified_at')
    op.drop_column('donations', 'notes')
    
    # Update status enum values: PENDING -> COMPLETED, VERIFIED -> CANCELLED
    op.execute("UPDATE donations SET status = 'COMPLETED' WHERE status = 'PENDING'")
    op.execute("UPDATE donations SET status = 'CANCELLED' WHERE status = 'VERIFIED'")
    
    # Update check constraint for donation status
    op.drop_constraint('chk_donation_status', 'donations', type_='check')
    op.create_check_constraint(
        'chk_donation_status',
        'donations',
        "status IN ('COMPLETED', 'CANCELLED', 'REJECTED')"
    )
    
    # Add check constraint for donation_type
    op.create_check_constraint(
        'chk_donation_type',
        'donations',
        "donation_type IN ('WHOLE_BLOOD', 'APHERESIS')"
    )
    
    # Backfill donation_type from request (default to WHOLE_BLOOD if no request)
    op.execute("""
        UPDATE donations d
        SET donation_type = COALESCE(
            (SELECT request_type FROM blood_requests br WHERE br.request_id = d.request_id),
            'WHOLE_BLOOD'
        )
        WHERE donation_type IS NULL
    """)
    op.alter_column('donations', 'donation_type', nullable=False)
    
    # Make request_id and commitment_id nullable (per roadmap)
    op.alter_column('donations', 'request_id', nullable=True)
    op.alter_column('donations', 'commitment_id', nullable=True)
    
    # Make verified_by non-nullable (per roadmap)
    op.alter_column('donations', 'verified_by', nullable=False)
    
    # ========== Notifications Table Changes ==========
    # Rename body to message
    op.alter_column('notifications', 'body', new_column_name='message')
    
    # Add is_read and is_push_sent columns
    op.add_column('notifications', sa.Column('is_read', sa.Boolean(), nullable=False, 
                                             server_default='false'))
    op.add_column('notifications', sa.Column('is_push_sent', sa.Boolean(), nullable=False, 
                                             server_default='false'))
    
    # Migrate status to is_read (READ -> true, others -> false)
    op.execute("UPDATE notifications SET is_read = true WHERE status = 'READ'")
    op.execute("UPDATE notifications SET is_push_sent = true WHERE status IN ('SENT', 'DELIVERED', 'READ')")
    
    # Drop status column and related timestamps
    op.drop_constraint('chk_notification_status', 'notifications', type_='check')
    op.drop_column('notifications', 'status')
    op.drop_column('notifications', 'sent_at')
    op.drop_column('notifications', 'delivered_at')
    
    # Drop commitment_id column (not in roadmap)
    op.drop_column('notifications', 'commitment_id')
    
    # Update indexes
    op.drop_index('idx_notifications_user', table_name='notifications')
    op.drop_index('idx_notifications_status', table_name='notifications')
    op.drop_index('idx_notifications_created', table_name='notifications')
    
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'], unique=False)
    op.create_index('idx_notifications_user_unread', 'notifications', ['user_id'], 
                    unique=False, postgresql_where=sa.text('is_read = false'))
    
    # Update foreign key constraints to match roadmap (ondelete CASCADE for user_id, SET NULL for others)
    op.drop_constraint('notifications_user_id_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key('notifications_user_id_fkey', 'notifications', 'users', 
                         ['user_id'], ['user_id'], ondelete='CASCADE')
    
    op.drop_constraint('notifications_request_id_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key('notifications_request_id_fkey', 'notifications', 'blood_requests', 
                         ['request_id'], ['request_id'], ondelete='SET NULL')
    
    op.drop_constraint('notifications_donation_id_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key('notifications_donation_id_fkey', 'notifications', 'donations', 
                         ['donation_id'], ['donation_id'], ondelete='SET NULL')


def downgrade() -> None:
    # ========== Notifications Table Rollback ==========
    # Restore foreign key constraints
    op.drop_constraint('notifications_donation_id_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key('notifications_donation_id_fkey', 'notifications', 'donations', 
                         ['donation_id'], ['donation_id'])
    
    op.drop_constraint('notifications_request_id_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key('notifications_request_id_fkey', 'notifications', 'blood_requests', 
                         ['request_id'], ['request_id'])
    
    op.drop_constraint('notifications_user_id_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key('notifications_user_id_fkey', 'notifications', 'users', 
                         ['user_id'], ['user_id'])
    
    # Restore indexes
    op.drop_index('idx_notifications_user_unread', table_name='notifications')
    op.drop_index('idx_notifications_user_read', table_name='notifications')
    op.create_index('idx_notifications_created', 'notifications', ['created_at'], unique=False)
    op.create_index('idx_notifications_status', 'notifications', ['status'], unique=False)
    op.create_index('idx_notifications_user', 'notifications', ['user_id'], unique=False)
    
    # Restore commitment_id column
    op.add_column('notifications', sa.Column('commitment_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('notifications_commitment_id_fkey', 'notifications', 'donation_commitments', 
                         ['commitment_id'], ['commitment_id'])
    
    # Restore status and timestamp columns
    op.add_column('notifications', sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('notifications', sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('notifications', sa.Column('status', sa.String(50), nullable=False, 
                                             server_default='PENDING'))
    
    # Migrate is_read back to status
    op.execute("UPDATE notifications SET status = 'READ' WHERE is_read = true")
    op.execute("UPDATE notifications SET status = 'SENT' WHERE is_read = false AND is_push_sent = true")
    
    op.create_check_constraint(
        'chk_notification_status',
        'notifications',
        "status IN ('PENDING', 'SENT', 'DELIVERED', 'READ', 'FAILED')"
    )
    
    # Drop is_read and is_push_sent columns
    op.drop_column('notifications', 'is_push_sent')
    op.drop_column('notifications', 'is_read')
    
    # Rename message back to body
    op.alter_column('notifications', 'message', new_column_name='body')
    
    # ========== Donations Table Rollback ==========
    op.alter_column('donations', 'verified_by', nullable=True)
    op.alter_column('donations', 'commitment_id', nullable=False)
    op.alter_column('donations', 'request_id', nullable=False)
    
    op.add_column('donations', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('donations', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))
    
    op.drop_column('donations', 'created_at')
    op.alter_column('donations', 'donation_date', new_column_name='donated_at')
    op.alter_column('donations', 'hero_points_earned', new_column_name='hero_points_awarded')
    
    op.drop_constraint('fk_donations_qr_id', 'donations', type_='foreignkey')
    op.drop_column('donations', 'qr_id')
    op.drop_constraint('chk_donation_type', 'donations', type_='check')
    op.drop_column('donations', 'donation_type')
    
    op.execute("UPDATE donations SET status = 'PENDING' WHERE status = 'COMPLETED'")
    op.execute("UPDATE donations SET status = 'VERIFIED' WHERE status = 'CANCELLED'")
    
    op.drop_constraint('chk_donation_status', 'donations', type_='check')
    op.create_check_constraint(
        'chk_donation_status',
        'donations',
        "status IN ('PENDING', 'VERIFIED', 'REJECTED')"
    )
    
    # ========== QR Codes Table Rollback ==========
    op.drop_index('idx_qr_codes_commitment', table_name='qr_codes')
    op.create_index('idx_qr_codes_expires', 'qr_codes', ['expires_at'], 
                    unique=False, postgresql_where=sa.text('is_used = false'))
    op.drop_index('idx_qr_codes_token', table_name='qr_codes')
    op.create_index('idx_qr_codes_string', 'qr_codes', ['qr_code_string'], unique=False)
    
    op.drop_constraint('fk_qr_codes_used_by', 'qr_codes', type_='foreignkey')
    op.drop_column('qr_codes', 'used_by')
    op.drop_column('qr_codes', 'signature')
    op.alter_column('qr_codes', 'token', new_column_name='qr_code_string')
