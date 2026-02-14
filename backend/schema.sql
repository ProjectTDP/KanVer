-- KanVer Database Schema
-- Blood Donation Platform Database

-- Enable PostGIS extension for geographic data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users Table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    date_of_birth DATE NOT NULL,
    blood_type VARCHAR(10) NOT NULL,
    
    -- Role and Verification
    role VARCHAR(50) DEFAULT 'USER' CHECK (role IN ('USER', 'NURSE', 'ADMIN')),
    is_verified BOOLEAN DEFAULT false,
    last_donation_date TIMESTAMPTZ,
    next_available_date TIMESTAMPTZ,
    
    -- Donation Statistics
    total_donations INT DEFAULT 0,
    location GEOGRAPHY(Point, 4326),
    hero_points INT DEFAULT 0,
    trust_score INT DEFAULT 100,
    no_show_count INT DEFAULT 0,
    
    -- Push Notifications
    fcm_token VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ
);

-- Hospitals Table
CREATE TABLE hospitals (
    hospital_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_name VARCHAR(255) NOT NULL,
    hospital_code VARCHAR(50) UNIQUE NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    address TEXT NOT NULL,
    
    -- Location Details
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    
    -- Configuration
    geofence_radius_meters INT DEFAULT 5000,
    has_blood_bank BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Hospital Staff Table
CREATE TABLE hospital_staff (
    staff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    staff_role VARCHAR(100),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint: One person cannot be added to the same hospital twice
    CONSTRAINT unique_hospital_staff UNIQUE (user_id, hospital_id)
);

-- Blood Requests Table
CREATE TABLE blood_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_code VARCHAR(20) UNIQUE NOT NULL,
    requester_id UUID NOT NULL REFERENCES users(user_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    
    -- Blood Details
    blood_type VARCHAR(10) NOT NULL,
    units_needed INT NOT NULL DEFAULT 1,
    units_collected INT NOT NULL DEFAULT 0,
    
    -- Request Type and Priority
    request_type VARCHAR(50) CHECK (request_type IN ('WHOLE_BLOOD', 'APHERESIS')),
    priority VARCHAR(50) DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'URGENT', 'CRITICAL')),
    
    -- Location
    location GEOGRAPHY(Point, 4326) NOT NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'FULFILLED', 'CANCELLED', 'EXPIRED')),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    fulfilled_at TIMESTAMPTZ
);

-- Donation Commitments Table
CREATE TABLE donation_commitments (
    commitment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES blood_requests(request_id),
    donor_id UUID NOT NULL REFERENCES users(user_id),
    
    -- Status Management
    status VARCHAR(50) DEFAULT 'ON_THE_WAY'
        CHECK (status IN ('ON_THE_WAY', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'TIMEOUT')),
    
    -- Timing
    committed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expected_arrival_time TIMESTAMPTZ,
    arrived_at TIMESTAMPTZ,
    
    -- Timeout Configuration
    timeout_minutes INT DEFAULT 60,
    cancel_reason TEXT,
    
    notes TEXT,
    
    -- Constraint: A donor cannot commit to the same request twice
    CONSTRAINT unique_donor_request_commitment UNIQUE (donor_id, request_id)
);

-- Donations Table
CREATE TABLE donations (
    donation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    request_id UUID REFERENCES blood_requests(request_id),
    commitment_id UUID REFERENCES donation_commitments(commitment_id),
    donor_id UUID NOT NULL REFERENCES users(user_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    verified_by UUID NOT NULL REFERENCES users(user_id),
    
    -- Donation Details
    blood_type VARCHAR(10) NOT NULL,
    donation_type VARCHAR(50) NOT NULL CHECK (donation_type IN ('WHOLE_BLOOD', 'APHERESIS')),
    units_donated INT DEFAULT 1,
    
    -- QR Code and Status
    qr_code VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'COMPLETED' CHECK (status IN ('COMPLETED', 'CANCELLED', 'REJECTED')),
    
    -- Rewards
    hero_points_earned INT DEFAULT 50,
    
    -- Timestamps
    donation_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- QR Codes Table
CREATE TABLE qr_codes (
    qr_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commitment_id UUID NOT NULL REFERENCES donation_commitments(commitment_id),
    
    -- QR Data
    token VARCHAR(255) UNIQUE NOT NULL,
    signature TEXT NOT NULL,
    
    -- Usage Status
    is_used BOOLEAN DEFAULT false,
    used_at TIMESTAMPTZ,
    used_by UUID REFERENCES users(user_id),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Constraint: Only one active QR per commitment
    CONSTRAINT unique_commitment_qr UNIQUE (commitment_id)
);

-- Notifications Table
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Notification Content
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Related Objects (Optional)
    request_id UUID REFERENCES blood_requests(request_id) ON DELETE SET NULL,
    donation_id UUID REFERENCES donations(donation_id) ON DELETE SET NULL,
    
    -- Read Status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    is_push_sent BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================

-- 1. Geographic (GIST) Indexes - Essential for location queries
CREATE INDEX idx_users_location ON users USING GIST(location) WHERE location IS NOT NULL;
CREATE INDEX idx_hospitals_location ON hospitals USING GIST(location);
CREATE INDEX idx_blood_requests_location ON blood_requests USING GIST(location);

-- 2. Partial (Conditional) Indexes - Performance optimization
CREATE INDEX idx_users_blood_type ON users(blood_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_notifications_unread ON notifications(user_id) WHERE is_read = false;
CREATE INDEX idx_qr_unused ON qr_codes(commitment_id) WHERE is_used = false;

-- 3. Business Logic Indexes
CREATE INDEX idx_blood_requests_composite ON blood_requests(status, blood_type, hospital_id);
CREATE INDEX idx_commitments_donor ON donation_commitments(donor_id);
CREATE INDEX idx_commitments_request ON donation_commitments(request_id);
CREATE INDEX idx_donations_donor ON donations(donor_id);
CREATE INDEX idx_donations_hospital ON donations(hospital_id);
CREATE INDEX idx_hospital_staff_user ON hospital_staff(user_id);
CREATE INDEX idx_hospital_staff_hospital ON hospital_staff(hospital_id);

-- 4. Timestamp Indexes for sorting and filtering
CREATE INDEX idx_blood_requests_created ON blood_requests(created_at DESC);
CREATE INDEX idx_donations_date ON donations(donation_date DESC);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
