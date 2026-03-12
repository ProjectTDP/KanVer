"""create tables

Revision ID: 002
Revises: 001
Create Date: 2025-02-20 00:01:00.000000

Bu migration, tüm veritabanı tablolarını oluşturur:
1. users
2. hospitals
3. hospital_staff
4. blood_requests
5. donation_commitments
6. qr_codes
7. donations
8. notifications
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
    """
    Tüm tabloları, enum'ları ve index'leri oluşturur.

    Oluşturma sırası foreign key bağımlılıklarına göre düzenlenmiştir.
    """

    # ========================================================================
    # 1. ENUM TYPES
    # ========================================================================

    op.execute("CREATE TYPE userrole AS ENUM ('USER', 'NURSE', 'ADMIN')")
    op.execute("CREATE TYPE requeststatus AS ENUM ('ACTIVE', 'FULFILLED', 'CANCELLED', 'EXPIRED')")
    op.execute("CREATE TYPE requesttype AS ENUM ('WHOLE_BLOOD', 'APHERESIS')")
    op.execute("CREATE TYPE priority AS ENUM ('LOW', 'NORMAL', 'URGENT', 'CRITICAL')")
    op.execute("CREATE TYPE commitmentstatus AS ENUM ('ON_THE_WAY', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'TIMEOUT')")
    op.execute("CREATE TYPE donationstatus AS ENUM ('COMPLETED', 'CANCELLED', 'REJECTED')")
    op.execute("CREATE TYPE notificationtype AS ENUM ('NEW_REQUEST', 'DONOR_FOUND', 'DONOR_ON_WAY', 'DONATION_COMPLETE', 'TIMEOUT_WARNING', 'NO_SHOW')")

    # ========================================================================
    # 2. TABLES
    # ========================================================================

    # --------------------------------------------------------------------
    # 2.1 users
    # --------------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', sa.VARCHAR(length=36), primary_key=True),
        sa.Column('phone_number', sa.VARCHAR(length=20), nullable=False),
        sa.Column('email', sa.VARCHAR(length=255), nullable=True),
        sa.Column('full_name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('password_hash', sa.VARCHAR(length=255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='USER'),
        sa.Column('blood_type', sa.VARCHAR(length=5), nullable=True),
        sa.Column('hero_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('trust_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('next_available_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_donations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('no_show_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('location', sa.Text(), nullable=True),  # PostGIS Geography
        sa.Column('location_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fcm_token', sa.VARCHAR(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Cast location to PostGIS Geography type
    op.execute("ALTER TABLE users ALTER COLUMN location TYPE geography(POINT, 4326) USING location::geography(POINT, 4326)")

    # Check constraints for users
    op.execute("ALTER TABLE users ADD CONSTRAINT check_hero_points_non_negative CHECK (hero_points >= 0)")
    op.execute("ALTER TABLE users ADD CONSTRAINT check_trust_score_range CHECK (trust_score >= 0 AND trust_score <= 100)")
    op.execute("ALTER TABLE users ADD CONSTRAINT check_total_donations_non_negative CHECK (total_donations >= 0)")
    op.execute("ALTER TABLE users ADD CONSTRAINT check_no_show_count_non_negative CHECK (no_show_count >= 0)")
    op.execute("ALTER TABLE users ADD CONSTRAINT check_blood_type_valid CHECK (blood_type IS NULL OR blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'))")
    op.execute("ALTER TABLE users ADD CONSTRAINT check_role_valid CHECK (role IN ('USER', 'NURSE', 'ADMIN'))")

    # --------------------------------------------------------------------
    # 2.2 hospitals
    # --------------------------------------------------------------------
    op.create_table(
        'hospitals',
        sa.Column('id', sa.VARCHAR(length=36), primary_key=True),
        sa.Column('hospital_code', sa.VARCHAR(length=20), unique=True, nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('district', sa.VARCHAR(length=100), nullable=False),
        sa.Column('city', sa.VARCHAR(length=100), nullable=False),
        sa.Column('location', sa.Text(), nullable=False),  # PostGIS Geography
        sa.Column('geofence_radius_meters', sa.Integer(), nullable=False, server_default='5000'),
        sa.Column('phone_number', sa.VARCHAR(length=20), nullable=False),
        sa.Column('email', sa.VARCHAR(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Cast location to PostGIS Geography type
    op.execute("ALTER TABLE hospitals ALTER COLUMN location TYPE geography(POINT, 4326) USING location::geography(POINT, 4326)")

    # Check constraint for hospitals
    op.execute("ALTER TABLE hospitals ADD CONSTRAINT check_geofence_radius_positive CHECK (geofence_radius_meters > 0)")

    # --------------------------------------------------------------------
    # 2.3 hospital_staff
    # --------------------------------------------------------------------
    op.create_table(
        'hospital_staff',
        sa.Column('id', sa.VARCHAR(length=36), primary_key=True),
        sa.Column('user_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('hospital_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Foreign keys for hospital_staff
    op.create_foreign_key(
        'fk_hospital_staff_user',
        'hospital_staff', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_hospital_staff_hospital',
        'hospital_staff', 'hospitals',
        ['hospital_id'], ['id'],
        ondelete='CASCADE'
    )

    # Unique constraint (user_id, hospital_id)
    op.create_unique_constraint('uq_hospital_staff_user_hospital', 'hospital_staff', ['user_id', 'hospital_id'])

    # --------------------------------------------------------------------
    # 2.4 blood_requests
    # --------------------------------------------------------------------
    op.create_table(
        'blood_requests',
        sa.Column('id', sa.VARCHAR(length=36), primary_key=True),
        sa.Column('request_code', sa.VARCHAR(length=20), unique=True, nullable=False),
        sa.Column('requester_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('hospital_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('blood_type', sa.VARCHAR(length=5), nullable=False),
        sa.Column('request_type', sa.String(20), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False, server_default='NORMAL'),
        sa.Column('units_needed', sa.Integer(), nullable=False),
        sa.Column('units_collected', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('location', sa.Text(), nullable=False),  # PostGIS Geography
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_name', sa.VARCHAR(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Cast location to PostGIS Geography type
    op.execute("ALTER TABLE blood_requests ALTER COLUMN location TYPE geography(POINT, 4326) USING location::geography(POINT, 4326)")

    # Foreign keys for blood_requests
    op.create_foreign_key(
        'fk_blood_requests_requester',
        'blood_requests', 'users',
        ['requester_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_blood_requests_hospital',
        'blood_requests', 'hospitals',
        ['hospital_id'], ['id'],
        ondelete='CASCADE'
    )

    # Check constraints for blood_requests
    op.execute("ALTER TABLE blood_requests ADD CONSTRAINT check_units_needed_positive CHECK (units_needed > 0)")
    op.execute("ALTER TABLE blood_requests ADD CONSTRAINT check_units_collected_non_negative CHECK (units_collected >= 0)")
    op.execute("ALTER TABLE blood_requests ADD CONSTRAINT check_units_collected_not_exceed_needed CHECK (units_collected <= units_needed)")
    op.execute("ALTER TABLE blood_requests ADD CONSTRAINT check_br_blood_type_valid CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'))")
    op.execute("ALTER TABLE blood_requests ADD CONSTRAINT check_request_type_valid CHECK (request_type IN ('WHOLE_BLOOD', 'APHERESIS'))")
    op.execute("ALTER TABLE blood_requests ADD CONSTRAINT check_status_valid CHECK (status IN ('ACTIVE', 'FULFILLED', 'CANCELLED', 'EXPIRED'))")
    op.execute("ALTER TABLE blood_requests ADD CONSTRAINT check_priority_valid CHECK (priority IN ('LOW', 'NORMAL', 'URGENT', 'CRITICAL'))")

    # --------------------------------------------------------------------
    # 2.5 donation_commitments
    # --------------------------------------------------------------------
    op.create_table(
        'donation_commitments',
        sa.Column('id', sa.VARCHAR(length=36), primary_key=True),
        sa.Column('donor_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('blood_request_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='ON_THE_WAY'),
        sa.Column('timeout_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('arrived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Foreign keys for donation_commitments
    op.create_foreign_key(
        'fk_commitments_donor',
        'donation_commitments', 'users',
        ['donor_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_commitments_blood_request',
        'donation_commitments', 'blood_requests',
        ['blood_request_id'], ['id'],
        ondelete='CASCADE'
    )

    # Check constraint for donation_commitments
    op.execute("ALTER TABLE donation_commitments ADD CONSTRAINT check_timeout_minutes_positive CHECK (timeout_minutes > 0)")
    op.execute("ALTER TABLE donation_commitments ADD CONSTRAINT check_commitment_status_valid CHECK (status IN ('ON_THE_WAY', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'TIMEOUT'))")

    # --------------------------------------------------------------------
    # 2.6 qr_codes
    # --------------------------------------------------------------------
    op.create_table(
        'qr_codes',
        sa.Column('id', sa.VARCHAR(length=36), primary_key=True),
        sa.Column('commitment_id', sa.VARCHAR(length=36), unique=True, nullable=False),
        sa.Column('token', sa.VARCHAR(length=255), unique=True, nullable=False),
        sa.Column('signature', sa.VARCHAR(length=255), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Foreign key for qr_codes
    op.create_foreign_key(
        'fk_qr_codes_commitment',
        'qr_codes', 'donation_commitments',
        ['commitment_id'], ['id'],
        ondelete='CASCADE'
    )

    # Check constraint for qr_codes
    op.execute("ALTER TABLE qr_codes ADD CONSTRAINT check_signature_not_null CHECK (signature IS NOT NULL)")

    # --------------------------------------------------------------------
    # 2.7 donations
    # --------------------------------------------------------------------
    op.create_table(
        'donations',
        sa.Column('id', sa.VARCHAR(length=36), primary_key=True),
        sa.Column('donor_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('hospital_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('blood_request_id', sa.VARCHAR(length=36), nullable=True),
        sa.Column('commitment_id', sa.VARCHAR(length=36), unique=True, nullable=True),
        sa.Column('qr_code_id', sa.VARCHAR(length=36), unique=True, nullable=True),
        sa.Column('donation_type', sa.String(20), nullable=False),
        sa.Column('blood_type', sa.VARCHAR(length=5), nullable=False),
        sa.Column('verified_by', sa.VARCHAR(length=36), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hero_points_earned', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('status', sa.String(20), nullable=False, server_default='COMPLETED'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Foreign keys for donations
    op.create_foreign_key(
        'fk_donations_donor',
        'donations', 'users',
        ['donor_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_donations_hospital',
        'donations', 'hospitals',
        ['hospital_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_donations_blood_request',
        'donations', 'blood_requests',
        ['blood_request_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_donations_commitment',
        'donations', 'donation_commitments',
        ['commitment_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_donations_qr_code',
        'donations', 'qr_codes',
        ['qr_code_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_donations_verified_by',
        'donations', 'users',
        ['verified_by'], ['id'],
        ondelete='SET NULL'
    )

    # Check constraints for donations
    op.execute("ALTER TABLE donations ADD CONSTRAINT check_hero_points_earned_non_negative CHECK (hero_points_earned >= 0)")
    op.execute("ALTER TABLE donations ADD CONSTRAINT check_donation_type_valid CHECK (donation_type IN ('WHOLE_BLOOD', 'APHERESIS'))")
    op.execute("ALTER TABLE donations ADD CONSTRAINT check_donations_blood_type_valid CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'))")
    op.execute("ALTER TABLE donations ADD CONSTRAINT check_donation_status_valid CHECK (status IN ('COMPLETED', 'CANCELLED', 'REJECTED'))")

    # --------------------------------------------------------------------
    # 2.8 notifications
    # --------------------------------------------------------------------
    op.create_table(
        'notifications',
        sa.Column('id', sa.VARCHAR(length=36), primary_key=True),
        sa.Column('user_id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('blood_request_id', sa.VARCHAR(length=36), nullable=True),
        sa.Column('donation_id', sa.VARCHAR(length=36), nullable=True),
        sa.Column('title', sa.VARCHAR(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_push_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('push_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fcm_token', sa.VARCHAR(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Foreign keys for notifications
    op.create_foreign_key(
        'fk_notifications_user',
        'notifications', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_notifications_blood_request',
        'notifications', 'blood_requests',
        ['blood_request_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_notifications_donation',
        'notifications', 'donations',
        ['donation_id'], ['id'],
        ondelete='SET NULL'
    )

    # Check constraint for notifications
    op.execute("ALTER TABLE notifications ADD CONSTRAINT check_notification_type_valid CHECK (notification_type IN ('NEW_REQUEST', 'DONOR_FOUND', 'DONOR_ON_WAY', 'DONATION_COMPLETE', 'TIMEOUT_WARNING', 'NO_SHOW'))")

    # ========================================================================
    # 3. INDEXES
    # ========================================================================

    # --------------------------------------------------------------------
    # 3.1 PostGIS GIST indexes
    # --------------------------------------------------------------------
    op.execute("CREATE INDEX idx_users_location ON users USING GIST (location)")
    op.execute("CREATE INDEX idx_hospitals_location ON hospitals USING GIST (location)")
    op.execute("CREATE INDEX idx_blood_requests_location ON blood_requests USING GIST (location)")

    # --------------------------------------------------------------------
    # 3.2 Partial unique indexes for users
    # --------------------------------------------------------------------
    # Phone number unique (only for non-deleted users)
    op.execute("CREATE UNIQUE INDEX idx_users_phone_unique ON users(phone_number) WHERE deleted_at IS NULL")

    # Email unique (only for non-deleted users with non-null email)
    op.execute("CREATE UNIQUE INDEX idx_users_email_unique ON users(email) WHERE email IS NOT NULL AND deleted_at IS NULL")

    # --------------------------------------------------------------------
    # 3.3 Single active commitment index
    # --------------------------------------------------------------------
    # A user can have only one active commitment at a time
    op.execute("""
        CREATE UNIQUE INDEX idx_single_active_commitment
        ON donation_commitments(donor_id)
        WHERE status IN ('ON_THE_WAY', 'ARRIVED')
    """)

    # --------------------------------------------------------------------
    # 3.4 Other indexes
    # --------------------------------------------------------------------
    # Hospitals
    op.create_index('idx_hospitals_code', 'hospitals', ['hospital_code'])

    # Blood requests
    op.create_index('idx_blood_requests_code', 'blood_requests', ['request_code'])
    op.create_index('idx_blood_requests_status', 'blood_requests', ['status'])
    op.create_index('idx_blood_requests_blood_type', 'blood_requests', ['blood_type'])
    op.create_index('idx_blood_requests_expires_at', 'blood_requests', ['expires_at'])

    # Donation commitments
    op.create_index('idx_commitments_donor_status', 'donation_commitments', ['donor_id', 'status'])
    op.create_index('idx_commitments_request', 'donation_commitments', ['blood_request_id'])
    op.create_index('idx_commitments_status', 'donation_commitments', ['status'])

    # QR codes
    op.create_index('idx_qr_codes_token', 'qr_codes', ['token'])
    op.create_index('idx_qr_codes_expires_at', 'qr_codes', ['expires_at'])

    # Donations
    op.create_index('idx_donations_donor', 'donations', ['donor_id'])
    op.create_index('idx_donations_hospital', 'donations', ['hospital_id'])
    op.create_index('idx_donations_created_at', 'donations', ['created_at'])

    # Notifications
    op.create_index('idx_notifications_user', 'notifications', ['user_id'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])


def downgrade() -> None:
    """
    Tüm tabloları, enum'ları ve index'leri kaldırır.

    Kaldırma sırası foreign key bağımlılıklarına göre tersinedir.
    """

    # ========================================================================
    # 1. DROP INDEXES
    # ========================================================================

    # PostGIS GIST indexes
    op.execute("DROP INDEX IF EXISTS idx_users_location")
    op.execute("DROP INDEX IF EXISTS idx_hospitals_location")
    op.execute("DROP INDEX IF EXISTS idx_blood_requests_location")

    # Partial unique indexes
    op.execute("DROP INDEX IF EXISTS idx_users_phone_unique")
    op.execute("DROP INDEX IF EXISTS idx_users_email_unique")
    op.execute("DROP INDEX IF EXISTS idx_single_active_commitment")

    # Other indexes
    op.execute("DROP INDEX IF EXISTS idx_hospitals_code")
    op.execute("DROP INDEX IF EXISTS idx_blood_requests_code")
    op.execute("DROP INDEX IF EXISTS idx_blood_requests_status")
    op.execute("DROP INDEX IF EXISTS idx_blood_requests_blood_type")
    op.execute("DROP INDEX IF EXISTS idx_blood_requests_expires_at")
    op.execute("DROP INDEX IF EXISTS idx_commitments_donor_status")
    op.execute("DROP INDEX IF EXISTS idx_commitments_request")
    op.execute("DROP INDEX IF EXISTS idx_commitments_status")
    op.execute("DROP INDEX IF EXISTS idx_qr_codes_token")
    op.execute("DROP INDEX IF EXISTS idx_qr_codes_expires_at")
    op.execute("DROP INDEX IF EXISTS idx_donations_donor")
    op.execute("DROP INDEX IF EXISTS idx_donations_hospital")
    op.execute("DROP INDEX IF EXISTS idx_donations_created_at")
    op.execute("DROP INDEX IF EXISTS idx_notifications_user")
    op.execute("DROP INDEX IF EXISTS idx_notifications_is_read")
    op.execute("DROP INDEX IF EXISTS idx_notifications_created_at")

    # ========================================================================
    # 2. DROP TABLES
    # ========================================================================

    # Drop tables in reverse order (to respect FK dependencies)
    op.drop_table('notifications')
    op.drop_table('donations')
    op.drop_table('qr_codes')
    op.drop_table('donation_commitments')
    op.drop_table('blood_requests')
    op.drop_table('hospital_staff')
    op.drop_table('hospitals')
    op.drop_table('users')

    # ========================================================================
    # 3. DROP ENUM TYPES
    # ========================================================================

    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS donationstatus")
    op.execute("DROP TYPE IF EXISTS commitmentstatus")
    op.execute("DROP TYPE IF EXISTS priority")
    op.execute("DROP TYPE IF EXISTS requesttype")
    op.execute("DROP TYPE IF EXISTS requeststatus")
    op.execute("DROP TYPE IF EXISTS userrole")
