"""Initial schema with all tables

Revision ID: 001
Revises: 
Create Date: 2024-02-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('blood_type', sa.String(10), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='USER'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_donation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_available_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_donations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('location', geoalchemy2.Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('hero_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('trust_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('no_show_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fcm_token', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('USER', 'NURSE', 'ADMIN')", name='chk_user_role'),
        sa.CheckConstraint("blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')", name='chk_blood_type'),
    )
    
    # Create indexes for users table
    op.create_index('idx_users_phone_unique', 'users', ['phone_number'], unique=True, postgresql_where=sa.text('deleted_at IS NULL'), if_not_exists=True)
    op.create_index('idx_users_email_unique', 'users', ['email'], unique=True, postgresql_where=sa.text('email IS NOT NULL AND deleted_at IS NULL'), if_not_exists=True)
    op.create_index('idx_users_location', 'users', ['location'], postgresql_using='gist', postgresql_where=sa.text('location IS NOT NULL'), if_not_exists=True)
    op.create_index('idx_users_blood_type', 'users', ['blood_type'], postgresql_where=sa.text('deleted_at IS NULL'), if_not_exists=True)
    op.create_index('idx_users_phone', 'users', ['phone_number'], if_not_exists=True)
    op.create_index('idx_users_fcm', 'users', ['fcm_token'], postgresql_where=sa.text('fcm_token IS NOT NULL'), if_not_exists=True)
    
    # Create hospitals table
    op.create_table(
        'hospitals',
        sa.Column('hospital_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('hospital_name', sa.String(255), nullable=False),
        sa.Column('hospital_code', sa.String(50), nullable=False, unique=True),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('location', geoalchemy2.Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('district', sa.String(100), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('geofence_radius_meters', sa.Integer(), nullable=False, server_default='5000'),
        sa.Column('has_blood_bank', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes for hospitals table
    op.create_index('idx_hospitals_location', 'hospitals', ['location'], postgresql_using='gist', if_not_exists=True)
    op.create_index('idx_hospitals_city_district', 'hospitals', ['city', 'district'], if_not_exists=True)
    
    # Create hospital_staff table
    op.create_table(
        'hospital_staff',
        sa.Column('staff_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('hospital_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hospitals.hospital_id'), nullable=False),
        sa.Column('staff_role', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', 'hospital_id', name='unique_hospital_staff'),
    )
    
    # Create blood_requests table
    op.create_table(
        'blood_requests',
        sa.Column('request_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('request_code', sa.String(20), nullable=False, unique=True),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('hospital_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hospitals.hospital_id'), nullable=False),
        sa.Column('blood_type', sa.String(10), nullable=False),
        sa.Column('units_needed', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('units_collected', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(50), nullable=False, server_default='NORMAL'),
        sa.Column('location', geoalchemy2.Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fulfilled_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("request_type IN ('WHOLE_BLOOD', 'APHERESIS')", name='chk_request_type'),
        sa.CheckConstraint("priority IN ('LOW', 'NORMAL', 'URGENT', 'CRITICAL')", name='chk_priority'),
        sa.CheckConstraint("status IN ('ACTIVE', 'FULFILLED', 'CANCELLED', 'EXPIRED')", name='chk_request_status'),
        sa.CheckConstraint('units_needed > 0 AND units_collected >= 0', name='chk_units_valid'),
        sa.CheckConstraint('units_collected <= units_needed', name='chk_units_overflow'),
        sa.CheckConstraint('expires_at > created_at', name='chk_dates_valid'),
    )
    
    # Create indexes for blood_requests table
    op.create_index('idx_blood_requests_location', 'blood_requests', ['location'], postgresql_using='gist', if_not_exists=True)
    op.create_index('idx_blood_requests_composite', 'blood_requests', ['status', 'blood_type', 'hospital_id'], if_not_exists=True)
    op.create_index('idx_blood_requests_status', 'blood_requests', ['status'], if_not_exists=True)
    
    # Create donation_commitments table
    op.create_table(
        'donation_commitments',
        sa.Column('commitment_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('blood_requests.request_id'), nullable=False),
        sa.Column('donor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='ON_THE_WAY'),
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expected_arrival_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('arrived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timeout_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('cancel_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.CheckConstraint("status IN ('ON_THE_WAY', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'TIMEOUT')", name='chk_commitment_status'),
    )
    
    # Create indexes for donation_commitments table
    op.create_index('idx_single_active_commitment', 'donation_commitments', ['donor_id'], unique=True, postgresql_where=sa.text("status IN ('ON_THE_WAY', 'ARRIVED')"), if_not_exists=True)
    op.create_index('idx_commitments_timeout_scan', 'donation_commitments', ['status', 'committed_at'], if_not_exists=True)
    op.create_index('idx_commitments_status', 'donation_commitments', ['status'], if_not_exists=True)
    op.create_index('idx_commitments_donor', 'donation_commitments', ['donor_id'], if_not_exists=True)
    op.create_index('idx_commitments_request', 'donation_commitments', ['request_id'], if_not_exists=True)
    
    # Create qr_codes table
    op.create_table(
        'qr_codes',
        sa.Column('qr_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('commitment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('donation_commitments.commitment_id'), nullable=False, unique=True),
        sa.Column('qr_code_string', sa.String(255), nullable=False, unique=True),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('expires_at > created_at', name='chk_qr_dates_valid'),
    )
    
    # Create indexes for qr_codes table
    op.create_index('idx_qr_codes_string', 'qr_codes', ['qr_code_string'], if_not_exists=True)
    op.create_index('idx_qr_codes_expires', 'qr_codes', ['expires_at'], postgresql_where=sa.text('is_used = false'), if_not_exists=True)
    
    # Create donations table
    op.create_table(
        'donations',
        sa.Column('donation_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('commitment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('donation_commitments.commitment_id'), nullable=False, unique=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('blood_requests.request_id'), nullable=False),
        sa.Column('donor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('hospital_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('hospitals.hospital_id'), nullable=False),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=True),
        sa.Column('blood_type', sa.String(10), nullable=False),
        sa.Column('units_donated', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('hero_points_awarded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('donated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.CheckConstraint("status IN ('PENDING', 'VERIFIED', 'REJECTED')", name='chk_donation_status'),
        sa.CheckConstraint('units_donated > 0', name='chk_units_donated_positive'),
    )
    
    # Create indexes for donations table
    op.create_index('idx_donations_donor', 'donations', ['donor_id'], if_not_exists=True)
    op.create_index('idx_donations_hospital', 'donations', ['hospital_id'], if_not_exists=True)
    op.create_index('idx_donations_request', 'donations', ['request_id'], if_not_exists=True)
    op.create_index('idx_donations_status', 'donations', ['status'], if_not_exists=True)
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('notification_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('blood_requests.request_id'), nullable=True),
        sa.Column('commitment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('donation_commitments.commitment_id'), nullable=True),
        sa.Column('donation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('donations.donation_id'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('PENDING', 'SENT', 'DELIVERED', 'READ', 'FAILED')", name='chk_notification_status'),
    )
    
    # Create indexes for notifications table
    op.create_index('idx_notifications_user', 'notifications', ['user_id'], if_not_exists=True)
    op.create_index('idx_notifications_status', 'notifications', ['status'], if_not_exists=True)
    op.create_index('idx_notifications_created', 'notifications', ['created_at'], if_not_exists=True)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('notifications')
    op.drop_table('donations')
    op.drop_table('qr_codes')
    op.drop_table('donation_commitments')
    op.drop_table('blood_requests')
    op.drop_table('hospital_staff')
    op.drop_table('hospitals')
    op.drop_table('users')
    
    # Drop PostGIS extension
    op.execute('DROP EXTENSION IF EXISTS postgis')
