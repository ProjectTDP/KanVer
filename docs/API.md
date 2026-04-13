# KanVer API Documentation

> **Version:** 1.0.0
> **Base URL:** `http://localhost:8000/api` (Development) | `https://api.kanver.com/api` (Production)

---

## Overview

KanVer (Kan ve Yardım Ağı) is a location-based emergency blood donation platform that connects patients in need of blood with voluntary donors. This API provides endpoints for user management, blood requests, donation commitments, and hospital management.

### Key Features

- **JWT-based Authentication** - Secure access tokens with refresh capability
- **Location-based Matching** - PostGIS-powered geospatial queries
- **Real-time Notifications** - Firebase Cloud Messaging integration
- **Gamification** - Hero points and rank badges for donors

---

## Authentication

All authenticated endpoints require a Bearer token in the `Authorization` header.

### Getting Tokens

```http
POST /api/auth/login
Content-Type: application/json

{
  "phone_number": "+905551234567",
  "password": "yourpassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Using Tokens

```http
GET /api/users/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Lifetimes

| Token Type | Lifetime |
|------------|----------|
| Access Token | 30 minutes |
| Refresh Token | 7 days |

---

## Error Response Format

All errors follow a consistent format:

```json
{
  "detail": {
    "error": "Error message",
    "code": "ERROR_CODE",
    "status_code": 400
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists or conflict |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `COOLDOWN_ACTIVE` | 400 | Donor is in cooldown period |
| `ACTIVE_COMMITMENT` | 409 | Donor already has active commitment |
| `SLOT_FULL` | 409 | N+1 limit reached for request |

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login with phone/password | No |
| POST | `/api/auth/refresh` | Refresh access token | No |

#### Register User

```http
POST /api/auth/register
Content-Type: application/json

{
  "phone_number": "+905551234567",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "email": "john@example.com",  // Optional
  "date_of_birth": "1990-05-15T00:00:00Z",
  "blood_type": "A+"
}
```

**Response:** `201 Created`
```json
{
  "user": {
    "id": "uuid",
    "phone_number": "+905551234567",
    "full_name": "John Doe",
    "blood_type": "A+",
    "role": "USER",
    "hero_points": 0,
    "trust_score": 100
  },
  "tokens": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer"
  }
}
```

---

### Users

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/users/me` | Get current user profile | Yes |
| PATCH | `/api/users/me` | Update profile | Yes |
| DELETE | `/api/users/me` | Delete account (soft delete) | Yes |
| PATCH | `/api/users/me/location` | Update location | Yes |
| GET | `/api/users/me/stats` | Get user statistics | Yes |

#### Update Location

```http
PATCH /api/users/me/location
Authorization: Bearer <token>
Content-Type: application/json

{
  "latitude": 36.8969,
  "longitude": 30.7133
}
```

#### Get User Statistics

**Response:**
```json
{
  "hero_points": 150,
  "trust_score": 100,
  "total_donations": 3,
  "no_show_count": 0,
  "next_available_date": "2025-06-15T00:00:00Z",
  "last_donation_date": "2025-03-15T10:30:00Z",
  "is_in_cooldown": true,
  "cooldown_remaining_days": 87,
  "rank_badge": "Bronz Kahraman"
}
```

---

### Blood Requests

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/requests` | List requests (paginated) | Yes |
| POST | `/api/requests` | Create blood request | Yes |
| GET | `/api/requests/{id}` | Get request details | Yes |
| PATCH | `/api/requests/{id}` | Update request | Yes |
| DELETE | `/api/requests/{id}` | Cancel request | Yes |

#### Create Blood Request

> **Note:** Request must be created within hospital geofence (5km radius).

```http
POST /api/requests
Authorization: Bearer <token>
Content-Type: application/json

{
  "hospital_id": "uuid",
  "blood_type": "A+",
  "units_needed": 2,
  "request_type": "WHOLE_BLOOD",
  "priority": "NORMAL",
  "latitude": 36.8969,
  "longitude": 30.7133,
  "patient_name": "Jane Doe",  // Optional
  "notes": "Urgent need"  // Optional
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "request_code": "#KAN-001",
  "blood_type": "A+",
  "request_type": "WHOLE_BLOOD",
  "priority": "NORMAL",
  "units_needed": 2,
  "units_collected": 0,
  "status": "ACTIVE",
  "hospital": {
    "id": "uuid",
    "name": "Antalya Eğitim ve Araştırma Hastanesi",
    "district": "Muratpaşa",
    "city": "Antalya"
  },
  "requester": {
    "id": "uuid",
    "full_name": "John Doe",
    "phone_number": "+905551234567"
  }
}
```

#### Request Status Values

| Status | Description |
|--------|-------------|
| `ACTIVE` | Request is active and accepting donors |
| `FULFILLED` | Required units collected |
| `CANCELLED` | Request cancelled by requester or admin |
| `EXPIRED` | Request expired (passed expiry date) |

#### Priority Values

| Priority | Description |
|----------|-------------|
| `LOW` | Non-urgent |
| `NORMAL` | Standard urgency |
| `URGENT` | High urgency |
| `CRITICAL` | Emergency |

---

### Donors

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/donors/nearby` | List nearby requests | Yes |
| POST | `/api/donors/accept` | Accept request (commit) | Yes |
| GET | `/api/donors/me/commitment` | Get active commitment | Yes |
| PATCH | `/api/donors/me/commitment/{id}` | Update commitment status | Yes |
| GET | `/api/donors/history` | Get donation history | Yes |

#### Accept Request (Create Commitment)

```http
POST /api/donors/accept
Authorization: Bearer <token>
Content-Type: application/json

{
  "request_id": "uuid"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "status": "ON_THE_WAY",
  "timeout_minutes": 60,
  "committed_at": "2025-03-15T10:00:00Z",
  "expected_arrival_time": "2025-03-15T11:00:00Z",
  "remaining_time_minutes": 55,
  "donor": {
    "id": "uuid",
    "full_name": "John Doe",
    "blood_type": "O+",
    "phone_number": "+905551234567"
  },
  "blood_request": {
    "id": "uuid",
    "request_code": "#KAN-001",
    "blood_type": "A+",
    "hospital_name": "Test Hospital",
    "hospital_city": "Antalya"
  }
}
```

#### Update Commitment Status

```http
PATCH /api/donors/me/commitment/{commitment_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "ARRIVED"
}
```

**For cancellation:**
```json
{
  "status": "CANCELLED",
  "cancel_reason": "Emergency situation"
}
```

**Response (ARRIVED):**
```json
{
  "id": "uuid",
  "status": "ARRIVED",
  "arrived_at": "2025-03-15T10:30:00Z",
  "qr_code": {
    "token": "abc123...",
    "signature": "sha256hash...",
    "expires_at": "2025-03-15T12:30:00Z",
    "is_used": false,
    "qr_content": "token:commitment_id:signature"
  }
}
```

#### Commitment Status Values

| Status | Description |
|--------|-------------|
| `ON_THE_WAY` | Donor is heading to hospital |
| `ARRIVED` | Donor arrived at hospital |
| `COMPLETED` | Donation completed |
| `CANCELLED` | Donor cancelled |
| `TIMEOUT` | Donor didn't arrive in time |

---

### Donations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/donations/verify` | Verify QR and complete donation | NURSE |
| GET | `/api/donations/history` | Get donation history | Yes |
| GET | `/api/donations/stats` | Get donation statistics | Yes |

#### Verify Donation (Nurse)

```http
POST /api/donations/verify
Authorization: Bearer <nurse_token>
Content-Type: application/json

{
  "qr_token": "abc123..."
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "donation_type": "WHOLE_BLOOD",
  "blood_type": "O+",
  "hero_points_earned": 50,
  "status": "COMPLETED",
  "verified_at": "2025-03-15T10:45:00Z",
  "donor": {
    "id": "uuid",
    "full_name": "John Doe",
    "blood_type": "O+",
    "phone_number": "+905551234567"
  },
  "hospital": {
    "id": "uuid",
    "name": "Test Hospital",
    "district": "Muratpaşa",
    "city": "Antalya"
  }
}
```

---

### Hospitals

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/hospitals` | List hospitals | No |
| GET | `/api/hospitals/nearby` | List nearby hospitals | No |
| GET | `/api/hospitals/{id}` | Get hospital details | No |
| POST | `/api/hospitals` | Create hospital | ADMIN |
| PATCH | `/api/hospitals/{id}` | Update hospital | ADMIN |
| POST | `/api/hospitals/{id}/staff` | Assign staff | ADMIN |
| DELETE | `/api/hospitals/{id}/staff/{staff_id}` | Remove staff | ADMIN |
| GET | `/api/hospitals/{id}/staff` | List hospital staff | ADMIN/NURSE |

#### List Nearby Hospitals

```http
GET /api/hospitals/nearby?latitude=36.8969&longitude=30.7133&radius_km=10
```

**Response:**
```json
[
  {
    "id": "uuid",
    "hospital_code": "AKD-001",
    "name": "Antalya Eğitim ve Araştırma Hastanesi",
    "address": "Konyaaltı Cad. No: 101",
    "district": "Muratpaşa",
    "city": "Antalya",
    "phone_number": "+902422494400",
    "geofence_radius_meters": 5000,
    "distance_km": 2.5,
    "is_active": true
  }
]
```

---

### Notifications

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/notifications` | List notifications | Yes |
| GET | `/api/notifications/unread-count` | Get unread count | Yes |
| PATCH | `/api/notifications/read` | Mark as read | Yes |
| PATCH | `/api/notifications/read-all` | Mark all as read | Yes |

#### List Notifications

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "notification_type": "DONATION_COMPLETE",
      "title": "Bağış Tamamlandı!",
      "message": "Bağışınız başarıyla tamamlandı. 50 kahramanlık puanı kazandınız!",
      "is_read": false,
      "created_at": "2025-03-15T10:45:00Z"
    }
  ],
  "total": 5,
  "unread_count": 2
}
```

#### Notification Types

| Type | Description |
|------|-------------|
| `NEW_REQUEST` | New blood request nearby |
| `DONOR_FOUND` | A donor accepted your request |
| `DONOR_ON_WAY` | Donor is on the way |
| `DONOR_ARRIVED` | Donor arrived at hospital |
| `DONATION_COMPLETE` | Donation completed |
| `REQUEST_FULFILLED` | Request fully satisfied |
| `TIMEOUT_WARNING` | Commitment timeout warning |
| `NO_SHOW` | No-show penalty applied |
| `REDIRECT_TO_BANK` | Redirected to blood bank |

---

### Admin

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/admin/stats` | System statistics | ADMIN |
| GET | `/api/admin/users` | List users | ADMIN |
| PATCH | `/api/admin/users/{id}` | Update user | ADMIN |
| GET | `/api/admin/requests` | List all requests | ADMIN |
| GET | `/api/admin/donations` | List all donations | ADMIN |

#### System Statistics

**Response:**
```json
{
  "total_users": 1250,
  "active_requests": 15,
  "today_donations": 23,
  "total_donations": 456,
  "avg_trust_score": 94.5,
  "blood_type_distribution": {
    "A+": 350,
    "A-": 50,
    "B+": 280,
    "B-": 45,
    "AB+": 30,
    "AB-": 15,
    "O+": 420,
    "O-": 60
  }
}
```

---

## Gamification

### Hero Points

| Donation Type | Points Earned |
|---------------|---------------|
| Whole Blood (WHOLE_BLOOD) | +50 |
| Apheresis (APHERESIS) | +100 |
| No-Show (Timeout) | -10 (trust score) |

### Rank Badges

| Points | Badge |
|--------|-------|
| 0-49 | Yeni Kahraman (New Hero) |
| 50-199 | Bronz Kahraman (Bronze Hero) |
| 200-499 | Gümüş Kahraman (Silver Hero) |
| 500-999 | Altın Kahraman (Gold Hero) |
| 1000+ | Platin Kahraman (Platinum Hero) |

### Cooldown Periods

| Donation Type | Cooldown |
|---------------|----------|
| Whole Blood | 90 days |
| Apheresis | 48 hours |

---

## Blood Type Compatibility

### Donor Compatibility (Who can donate to whom)

| Donor Type | Can Donate To |
|------------|---------------|
| O- | O-, O+, A-, A+, B-, B+, AB-, AB+ (Universal Donor) |
| O+ | O+, A+, B+, AB+ |
| A- | A-, A+, AB-, AB+ |
| A+ | A+, AB+ |
| B- | B-, B+, AB-, AB+ |
| B+ | B+, AB+ |
| AB- | AB-, AB+ |
| AB+ | AB+ (Universal Recipient) |

---

## N+1 Rule

To handle race conditions when multiple donors accept a request:

- If `units_needed = N`, maximum `N + 1` donors can accept
- First donor to complete donation fills the slot
- Additional donors are redirected to general blood bank

**Example:**
- Request for 1 unit (N=1)
- Maximum 2 donors can accept
- 3rd donor receives "Slot full" error

---

## Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| Auth endpoints | 10 requests/minute |
| General endpoints | 100 requests/minute |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests
- `X-RateLimit-Remaining`: Remaining requests
- `Retry-After`: Seconds until reset (if limited)

---

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-03-15T10:00:00Z"
}
```

```http
GET /health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## Support

For API support, please contact:
- **Email:** api@kanver.com
- **GitHub Issues:** https://github.com/kanver/api/issues