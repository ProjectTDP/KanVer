"""add blood request code sequence

Revision ID: 8f9a6c3d1b20
Revises: 442f47db67bf
Create Date: 2026-03-13 17:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "8f9a6c3d1b20"
down_revision = "442f47db67bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create sequence for race-safe blood request code generation."""
    op.execute("CREATE SEQUENCE IF NOT EXISTS blood_request_code_seq")

    op.execute(
        """
        DO $$
        DECLARE
            max_code INTEGER;
        BEGIN
            SELECT MAX(CAST(substring(request_code FROM 6) AS INTEGER))
            INTO max_code
            FROM blood_requests
            WHERE request_code ~ '^#KAN-[0-9]+$';

            IF max_code IS NULL THEN
                PERFORM setval('blood_request_code_seq', 1, false);
            ELSE
                PERFORM setval('blood_request_code_seq', max_code, true);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Drop request code sequence."""
    op.execute("DROP SEQUENCE IF EXISTS blood_request_code_seq")
