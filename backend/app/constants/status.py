"""
Status Constants for Blood Requests, Commitments, and Donations
"""

from enum import Enum


class RequestStatus(str, Enum):
    """Blood request status enumeration"""
    
    ACTIVE = "ACTIVE"          # Request is active and accepting donors
    FULFILLED = "FULFILLED"    # Request has been fulfilled (units_collected >= units_needed)
    CANCELLED = "CANCELLED"    # Request was cancelled by requester
    EXPIRED = "EXPIRED"        # Request expired (expires_at < now)


class RequestType(str, Enum):
    """Blood donation type enumeration"""
    
    WHOLE_BLOOD = "WHOLE_BLOOD"  # Whole blood donation (90 day cooldown)
    APHERESIS = "APHERESIS"      # Apheresis/platelet donation (48 hour cooldown)


class Priority(str, Enum):
    """Blood request priority level"""
    
    LOW = "LOW"              # Non-urgent, can wait
    NORMAL = "NORMAL"        # Standard priority
    URGENT = "URGENT"        # Urgent, needs attention soon
    CRITICAL = "CRITICAL"    # Critical, immediate attention required


class CommitmentStatus(str, Enum):
    """Donation commitment status enumeration"""
    
    ON_THE_WAY = "ON_THE_WAY"  # Donor committed and is on the way
    ARRIVED = "ARRIVED"        # Donor arrived at hospital
    COMPLETED = "COMPLETED"    # Donation completed successfully
    CANCELLED = "CANCELLED"    # Commitment cancelled by donor
    TIMEOUT = "TIMEOUT"        # Commitment timed out (no-show)


class DonationStatus(str, Enum):
    """Completed donation status enumeration"""
    
    PENDING = "PENDING"        # Donation pending verification
    VERIFIED = "VERIFIED"      # Donation verified by nurse
    REJECTED = "REJECTED"      # Donation was rejected (medical reasons)


class NotificationStatus(str, Enum):
    """Notification delivery status enumeration"""
    
    PENDING = "PENDING"        # Notification queued, not sent yet
    SENT = "SENT"              # Notification sent to FCM
    DELIVERED = "DELIVERED"    # Notification delivered to device
    READ = "READ"              # Notification read by user
    FAILED = "FAILED"          # Notification failed to send


class NotificationType(str, Enum):
    """Notification type enumeration"""
    
    # Blood Request Notifications
    NEW_REQUEST = "NEW_REQUEST"                    # New blood request nearby
    REQUEST_FULFILLED = "REQUEST_FULFILLED"        # Your request was fulfilled
    REQUEST_CANCELLED = "REQUEST_CANCELLED"        # Request was cancelled
    REQUEST_EXPIRED = "REQUEST_EXPIRED"            # Request expired
    
    # Commitment Notifications
    DONOR_FOUND = "DONOR_FOUND"                    # A donor committed to your request
    DONOR_ON_WAY = "DONOR_ON_WAY"                  # Donor is on the way
    DONOR_ARRIVED = "DONOR_ARRIVED"                # Donor arrived at hospital
    COMMITMENT_CANCELLED = "COMMITMENT_CANCELLED"  # Donor cancelled commitment
    
    # Donation Notifications
    DONATION_COMPLETE = "DONATION_COMPLETE"        # Donation completed, hero points earned
    REDIRECT_TO_BANK = "REDIRECT_TO_BANK"          # Excess donor redirected to general blood bank
    
    # Timeout & No-Show Notifications
    TIMEOUT_WARNING = "TIMEOUT_WARNING"            # Commitment timeout warning
    NO_SHOW = "NO_SHOW"                            # Commitment timed out (no-show penalty)
    
    # Gamification Notifications
    HERO_POINTS_EARNED = "HERO_POINTS_EARNED"      # Hero points awarded
    RANK_UP = "RANK_UP"                            # User rank increased
    TRUST_SCORE_CHANGED = "TRUST_SCORE_CHANGED"    # Trust score changed
    
    # System Notifications
    ACCOUNT_VERIFIED = "ACCOUNT_VERIFIED"          # Account verified
    COOLDOWN_ENDED = "COOLDOWN_ENDED"              # Cooldown period ended
    SYSTEM_ANNOUNCEMENT = "SYSTEM_ANNOUNCEMENT"    # System-wide announcement


# All valid statuses as lists
ALL_REQUEST_STATUSES = [status.value for status in RequestStatus]
ALL_REQUEST_TYPES = [rtype.value for rtype in RequestType]
ALL_PRIORITIES = [priority.value for priority in Priority]
ALL_COMMITMENT_STATUSES = [status.value for status in CommitmentStatus]
ALL_DONATION_STATUSES = [status.value for status in DonationStatus]
ALL_NOTIFICATION_STATUSES = [status.value for status in NotificationStatus]
ALL_NOTIFICATION_TYPES = [ntype.value for ntype in NotificationType]
