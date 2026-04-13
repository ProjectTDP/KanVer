# KanVer Database Schema Documentation

> **Database:** PostgreSQL 15+ with PostGIS extension
> **Schema Version:** 1.0.0
> **Last Updated:** 2025-03-15

---

## Overview

KanVer uses PostgreSQL with the PostGIS extension for geospatial data handling. The database consists of 8 core tables designed to support a location-based blood donation platform.

### Key Features

- **Geospatial Indexing** - GIST indexes for fast location queries
- **Soft Delete** - Users can be soft-deleted while preserving data integrity
- **Partial Unique Indexes** - Prevent duplicates while allowing soft deletes
- **Check Constraints** - Data integrity enforcement at database level

---

## ER Diagram

```
                                    ┌─────────────────┐
                                    │    hospitals    │
                                    ├─────────────────┤
                                    │ id (PK)         │
                                    │ hospital_code   │
                                    │ name            │
                                    │ location (GIST) │
                                    │ geofence_radius │
                                    └────────┬────────┘
                                             │
         ┌───────────────────────────────────┼───────────────────────────────────┐
         │                                   │                                   │
         │    ┌─────────────────┐    ┌───────┴───────┐    ┌─────────────────┐   │
         │    │ hospital_staff  │    │ blood_requests│    │   donations     │   │
         │    ├─────────────────┤    ├───────────────┤    ├─────────────────┤   │
         │    │ id (PK)         │    │ id (PK)       │    │ id (PK)         │   │
         │    │ user_id (FK) ───┼────│ hospital_id   │    │ hospital_id     │   │
         │    │ hospital_id(FK) │    │ requester_id  │    │ donor_id        │   │
         │    └────────┬────────┘    │ blood_type    │    │ blood_request_id│   │
         │             │             │ units_needed  │    │ commitment_id   │   │
         │             │             │ status        │    │ qr_code_id      │   │
         │             │             └───────┬───────┘    └────────┬────────┘   │
         │             │                     │                     │            │
         │             │             ┌───────┴───────┐              │            │
         │             │             │               │              │            │
         │             │    ┌────────┴─────┐ ┌──────┴──────┐       │            │
         │             │    │donation_     │ │  qr_codes   │       │            │
         │             │    │commitments   │ ├─────────────┤       │            │
         │             │    ├──────────────┤ │ id (PK)     │       │            │
         │             │    │ id (PK)      │ │ commitment_id│───────┘            │
         │             │    │ donor_id     │ │ token       │                    │
         │             │    │ blood_req_id │ │ signature   │                    │
         │             │    │ status       │ │ is_used     │                    │
         │             │    └──────┬───────┘ └─────────────┘                    │
         │             │           │                                            │
         │             │           │    ┌─────────────────┐                     │
         │             │           │    │  notifications  │                     │
         │             │           │    ├─────────────────┤                     │
         │             │           │    │ id (PK)         │                     │
         │             │           │    │ user_id         │                     │
         │             │           │    │ blood_request_id│                     │
         │             │           │    │ donation_id     │                     │
         │             │           │    └─────────────────┘                     │
         │             │           │                                            │
┌────────┴─────────────┴───────────┴────────────────────────────────────────────┘
│
│   ┌─────────────────┐
│   │     users       │
│   ├─────────────────┤
│   │ id (PK)         │
│   │ phone_number    │
│   │ full_name       │
│   │ blood_type      │
│   │ role            │
│   │ hero_points     │
│   │ trust_score     │
│   │ location (GIST) │
│   │ last_donation   │
│   │ next_available  │
│   └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────
```

---

## Tables

### 1. users

Primary user table storing donor and requester information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID |
| `phone_number` | VARCHAR(20) | NOT NULL | Unique (soft delete protected) |
| `email` | VARCHAR(255) | NULLABLE | Unique (soft delete protected) |
| `full_name` | VARCHAR(255) | NOT NULL | User's full name |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash |
| `date_of_birth` | TIMESTAMPTZ | NOT NULL | For 18+ validation |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'USER' | USER, NURSE, ADMIN |
| `blood_type` | VARCHAR(5) | NULLABLE | A+, A-, B+, B-, AB+, AB-, O+, O- |
| `hero_points` | INTEGER | NOT NULL, DEFAULT 0 | Gamification points |
| `trust_score` | INTEGER | NOT NULL, DEFAULT 100 | 0-100 range |
| `last_donation_date` | TIMESTAMPTZ | NULLABLE | For cooldown calculation |
| `next_available_date` | TIMESTAMPTZ | NULLABLE | Cooldown end date |
| `total_donations` | INTEGER | NOT NULL, DEFAULT 0 | Count |
| `no_show_count` | INTEGER | NOT NULL, DEFAULT 0 | Missed commitments |
| `location` | GEOGRAPHY(POINT, 4326) | NULLABLE | PostGIS point |
| `location_updated_at` | TIMESTAMPTZ | NULLABLE | Last location update |
| `fcm_token` | VARCHAR(500) | NULLABLE | Firebase Cloud Messaging token |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Account status |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT FALSE | Verification status |
| `deleted_at` | TIMESTAMPTZ | NULLABLE | Soft delete timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Update timestamp |

#### Check Constraints

```sql
check_hero_points_non_negative: hero_points >= 0
check_trust_score_range: trust_score >= 0 AND trust_score <= 100
check_total_donations_non_negative: total_donations >= 0
check_no_show_count_non_negative: no_show_count >= 0
check_blood_type_valid: blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')
check_role_valid: role IN ('USER', 'NURSE', 'ADMIN')
```

#### Indexes

```sql
idx_users_location: GIST index on location
idx_users_phone_unique: UNIQUE on phone_number WHERE deleted_at IS NULL
idx_users_email_unique: UNIQUE on email WHERE email IS NOT NULL AND deleted_at IS NULL
```

---

### 2. hospitals

Hospital information with geofence radius.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID |
| `hospital_code` | VARCHAR(20) | UNIQUE, NOT NULL | Unique code (e.g., AKD-001) |
| `name` | VARCHAR(255) | NOT NULL | Hospital name |
| `address` | TEXT | NOT NULL | Full address |
| `district` | VARCHAR(100) | NOT NULL | District |
| `city` | VARCHAR(100) | NOT NULL | City |
| `location` | GEOGRAPHY(POINT, 4326) | NOT NULL | PostGIS point |
| `geofence_radius_meters` | INTEGER | NOT NULL, DEFAULT 5000 | Geofence radius |
| `phone_number` | VARCHAR(20) | NOT NULL | Contact phone |
| `email` | VARCHAR(255) | NULLABLE | Contact email |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Active status |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Update timestamp |

#### Indexes

```sql
idx_hospitals_location: GIST index on location
```

---

### 3. hospital_staff

Maps nurses to hospitals (many-to-many relationship).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID |
| `user_id` | VARCHAR(36) | FK → users.id, NOT NULL | Staff user |
| `hospital_id` | VARCHAR(36) | FK → hospitals.id, NOT NULL | Assigned hospital |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Assignment status |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Update timestamp |

#### Constraints

```sql
uq_hospital_staff_user_hospital: UNIQUE(user_id, hospital_id)
```

#### Indexes

```sql
idx_hospital_staff_user: INDEX on user_id
idx_hospital_staff_hospital: INDEX on hospital_id
```

---

### 4. blood_requests

Blood donation requests created by patients' relatives.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID |
| `request_code` | VARCHAR(20) | UNIQUE, NOT NULL | Human-readable code (#KAN-XXX) |
| `requester_id` | VARCHAR(36) | FK → users.id, NOT NULL | Request owner |
| `hospital_id` | VARCHAR(36) | FK → hospitals.id, NOT NULL | Target hospital |
| `blood_type` | VARCHAR(5) | NOT NULL | Required blood type |
| `request_type` | VARCHAR(20) | NOT NULL | WHOLE_BLOOD or APHERESIS |
| `priority` | VARCHAR(20) | NOT NULL, DEFAULT 'NORMAL' | LOW, NORMAL, URGENT, CRITICAL |
| `units_needed` | INTEGER | NOT NULL | Required units |
| `units_collected` | INTEGER | NOT NULL, DEFAULT 0 | Collected units |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'ACTIVE' | ACTIVE, FULFILLED, CANCELLED, EXPIRED |
| `location` | GEOGRAPHY(POINT, 4326) | NOT NULL | Request creation location |
| `expires_at` | TIMESTAMPTZ | NULLABLE | Expiry date |
| `patient_name` | VARCHAR(255) | NULLABLE | Optional patient name |
| `notes` | TEXT | NULLABLE | Additional notes |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Update timestamp |

#### Check Constraints

```sql
check_units_needed_positive: units_needed > 0
check_units_collected_non_negative: units_collected >= 0
check_units_collected_not_exceed_needed: units_collected <= units_needed
```

#### Indexes

```sql
idx_blood_requests_location: GIST index on location
idx_blood_requests_status: INDEX on status
idx_blood_requests_blood_type: INDEX on blood_type
idx_blood_requests_expires_at: INDEX on expires_at
```

---

### 5. donation_commitments

Tracks "I'm coming" commitments from donors.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID |
| `donor_id` | VARCHAR(36) | FK → users.id, NOT NULL | Donor user |
| `blood_request_id` | VARCHAR(36) | FK → blood_requests.id, NOT NULL | Related request |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'ON_THE_WAY' | Commitment status |
| `timeout_minutes` | INTEGER | NOT NULL, DEFAULT 60 | Timeout duration |
| `arrived_at` | TIMESTAMPTZ | NULLABLE | Arrival timestamp |
| `completed_at` | TIMESTAMPTZ | NULLABLE | Completion timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Update timestamp |

#### Status Values

| Status | Description |
|--------|-------------|
| `ON_THE_WAY` | Donor is heading to hospital |
| `ARRIVED` | Donor has arrived |
| `COMPLETED` | Donation completed |
| `CANCELLED` | Donor cancelled |
| `TIMEOUT` | Timeout expired (no-show) |

#### Indexes

```sql
idx_commitments_donor_status: INDEX on donor_id
idx_commitments_request: INDEX on blood_request_id
idx_commitments_status: INDEX on status
idx_single_active_commitment: UNIQUE on donor_id WHERE status IN ('ON_THE_WAY', 'ARRIVED')
```

> **Critical:** The `idx_single_active_commitment` index ensures a donor can only have one active commitment at a time.

---

### 6. qr_codes

Secure QR codes generated when donor arrives at hospital.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID |
| `commitment_id` | VARCHAR(36) | FK → donation_commitments.id, UNIQUE, NOT NULL | Related commitment |
| `token` | VARCHAR(255) | UNIQUE, NOT NULL | Random token |
| `signature` | VARCHAR(255) | NOT NULL | HMAC-SHA256 signature |
| `is_used` | BOOLEAN | NOT NULL, DEFAULT FALSE | Usage flag |
| `used_at` | TIMESTAMPTZ | NULLABLE | Usage timestamp |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Expiry timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Update timestamp |

#### Security Features

- **HMAC-SHA256 Signature** - Prevents token forgery
- **Time-based Expiry** - QR codes expire after 2 hours
- **One-time Use** - `is_used` flag prevents reuse

#### Indexes

```sql
idx_qr_codes_token: INDEX on token
idx_qr_codes_expires_at: INDEX on expires_at
```

---

### 7. donations

Completed donation records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID |
| `donor_id` | VARCHAR(36) | FK → users.id, NOT NULL | Donor user |
| `hospital_id` | VARCHAR(36) | FK → hospitals.id, NOT NULL | Hospital |
| `blood_request_id` | VARCHAR(36) | FK → blood_requests.id, NULLABLE | Related request |
| `commitment_id` | VARCHAR(36) | FK → donation_commitments.id, UNIQUE, NULLABLE | Related commitment |
| `qr_code_id` | VARCHAR(36) | FK → qr_codes.id, UNIQUE, NULLABLE | Related QR code |
| `donation_type` | VARCHAR(20) | NOT NULL | WHOLE_BLOOD or APHERESIS |
| `blood_type` | VARCHAR(5) | NOT NULL | Donor's blood type |
| `verified_by` | VARCHAR(36) | FK → users.id, NULLABLE | Nurse who verified |
| `verified_at` | TIMESTAMPTZ | NULLABLE | Verification timestamp |
| `hero_points_earned` | INTEGER | NOT NULL, DEFAULT 50 | Points earned |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'COMPLETED' | COMPLETED, CANCELLED, REJECTED |
| `notes` | TEXT | NULLABLE | Additional notes |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Update timestamp |

#### Indexes

```sql
idx_donations_donor: INDEX on donor_id
idx_donations_hospital: INDEX on hospital_id
idx_donations_verified_by: INDEX on verified_by
idx_donations_created_at: INDEX on created_at
```

---

### 8. notifications

User notification history.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID |
| `user_id` | VARCHAR(36) | FK → users.id, NOT NULL | Recipient |
| `notification_type` | VARCHAR(50) | NOT NULL | Type of notification |
| `blood_request_id` | VARCHAR(36) | FK → blood_requests.id, NULLABLE | Related request |
| `donation_id` | VARCHAR(36) | FK → donations.id, NULLABLE | Related donation |
| `title` | VARCHAR(255) | NOT NULL | Notification title |
| `message` | TEXT | NOT NULL | Notification message |
| `is_read` | BOOLEAN | NOT NULL, DEFAULT FALSE | Read status |
| `read_at` | TIMESTAMPTZ | NULLABLE | Read timestamp |
| `is_push_sent` | BOOLEAN | NOT NULL, DEFAULT FALSE | FCM sent status |
| `push_sent_at` | TIMESTAMPTZ | NULLABLE | FCM sent timestamp |
| `fcm_token` | VARCHAR(500) | NULLABLE | FCM token used |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Update timestamp |

#### Notification Types

| Type | Description |
|------|-------------|
| `NEW_REQUEST` | New blood request nearby |
| `DONOR_FOUND` | Donor accepted request |
| `DONOR_ON_WAY` | Donor is on the way |
| `DONOR_ARRIVED` | Donor arrived at hospital |
| `DONATION_COMPLETE` | Donation completed |
| `REQUEST_FULFILLED` | Request fully satisfied |
| `TIMEOUT_WARNING` | Commitment timeout warning |
| `NO_SHOW` | No-show penalty |
| `REDIRECT_TO_BANK` | Redirect to blood bank |

#### Indexes

```sql
idx_notifications_user: INDEX on user_id
idx_notifications_is_read: INDEX on is_read
idx_notifications_created_at: INDEX on created_at
```

---

## Relationships Summary

| Relationship | Type | Description |
|--------------|------|-------------|
| users → hospital_staff | 1:N | User can be assigned to multiple hospitals |
| hospitals → hospital_staff | 1:N | Hospital can have multiple staff |
| users → blood_requests | 1:N | User can create multiple requests |
| hospitals → blood_requests | 1:N | Hospital can have multiple requests |
| users → donation_commitments | 1:N | User can have multiple commitments |
| blood_requests → donation_commitments | 1:N | Request can have multiple commitments |
| donation_commitments → qr_codes | 1:1 | Each commitment has one QR code |
| donation_commitments → donations | 1:1 | Each commitment leads to one donation |
| users → donations | 1:N | User can have multiple donations |
| hospitals → donations | 1:N | Hospital can have multiple donations |
| users → notifications | 1:N | User can have multiple notifications |

---

## Database Functions

### Request Code Generation

```sql
-- Sequence for request codes
CREATE SEQUENCE blood_request_code_seq START 1;

-- Generate code: #KAN-001, #KAN-002, etc.
SELECT '#KAN-' || LPAD(nextval('blood_request_code_seq')::TEXT, 3, '0');
```

### Location Queries

```sql
-- Find hospitals within radius
SELECT * FROM hospitals
WHERE ST_DWithin(
    location,
    ST_MakePoint(longitude, latitude)::geography,
    radius_meters
);

-- Calculate distance
SELECT ST_Distance(
    location,
    ST_MakePoint(longitude, latitude)::geography
) / 1000 as distance_km
FROM hospitals;
```

---

## Migration History

| Version | Date | Description |
|---------|------|-------------|
| 20250220_0000 | 2025-02-20 | Initial PostGIS setup |
| 20250220_0001 | 2025-02-20 | Create all tables |
| 20260220_1320 | 2025-02-20 | Add date_of_birth to users |
| 20260313_1700 | 2025-03-13 | Add blood_request_code_sequence |
| 20260313_1735 | 2025-03-13 | Add last_donation_date to users |
| 20260315_1000 | 2025-03-15 | Add new notification types |
| 20260315_1100 | 2025-03-15 | Add is_verified to users |

---

## Performance Tips

### Index Usage

1. **GIST indexes** are used for geospatial queries (ST_DWithin, ST_Distance)
2. **B-tree indexes** are used for exact matches and ranges
3. **Partial unique indexes** enforce uniqueness while allowing soft deletes

### Query Optimization

```sql
-- Good: Uses GIST index
SELECT * FROM blood_requests
WHERE ST_DWithin(location, user_location, 10000)
AND status = 'ACTIVE';

-- Good: Uses composite conditions
SELECT * FROM donation_commitments
WHERE donor_id = :id
AND status IN ('ON_THE_WAY', 'ARRIVED');

-- Avoid: Full table scan
SELECT * FROM notifications WHERE message LIKE '%keyword%';
```

---

## Backup Strategy

### Recommended Backup Schedule

| Type | Frequency | Retention |
|------|-----------|-----------|
| Full backup | Daily | 7 days |
| Incremental | Hourly | 24 hours |
| WAL archiving | Continuous | 7 days |

### Backup Command

```bash
# Full backup
pg_dump -U kanver_user -d kanver_db -F c -f kanver_backup_$(date +%Y%m%d).dump

# Restore
pg_restore -U kanver_user -d kanver_db kanver_backup_20250315.dump
```

---

## Security Considerations

### Data Protection

1. **Password Hashing** - bcrypt with cost factor 12
2. **Sensitive Fields** - password_hash never returned in API responses
3. **Soft Delete** - User data retained but hidden from queries
4. **FCM Tokens** - Stored securely, can be revoked

### Access Control

1. **Role-based Access** - USER, NURSE, ADMIN roles
2. **Hospital Assignment** - Nurses can only verify at assigned hospitals
3. **Request Ownership** - Only requesters can modify their own requests

---

## Contact

For database-related questions:
- **DBA Team:** dba@kanver.com
- **Technical Support:** tech@kanver.com