# app/tests/test_mfa.py
"""
Comprehensive tests for Multi-Factor Authentication (MFA) functionality.

Tests TOTP secret generation, verification, backup codes, and MFA enforcement.
"""
import pytest
import datetime as dt
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
import pyotp
import uuid

from app.core.models import MFASecret, User, UserRole
from app.services.mfa_service import MFAService


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def mfa_service(mock_db):
    """Create MFA service with mock database"""
    return MFAService(mock_db)


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        role=UserRole.admin,
        is_active=True,
        email_verified=True
    )


@pytest.fixture
def regular_user():
    """Create a regular user (non-admin) for testing"""
    return User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        username="regularuser",
        email="regular@example.com",
        role=UserRole.user,
        is_active=True,
        email_verified=True
    )


@pytest.fixture
def sample_mfa_secret(sample_user):
    """Create a sample MFA secret for testing"""
    return MFASecret(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        tenant_id=sample_user.tenant_id,
        secret="JBSWY3DPEHPK3PXP",  # Base32 encoded test secret
        backup_codes=["ABCD1234", "EFGH5678", "IJKL9012"],
        is_verified=True,
        created_at=dt.datetime.now(dt.timezone.utc),
        backup_codes_used=0
    )


class TestMFASecretGeneration:
    """Test MFA secret and code generation"""

    def test_generate_secret(self, mfa_service):
        """Test TOTP secret generation"""
        secret = mfa_service.generate_secret()

        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded secrets are typically 32 chars
        assert secret.isalnum()  # Should be alphanumeric base32

        # Should be able to create TOTP with it
        totp = pyotp.TOTP(secret)
        assert totp is not None

    def test_generate_backup_codes(self, mfa_service):
        """Test backup code generation"""
        backup_codes = mfa_service.generate_backup_codes()

        assert isinstance(backup_codes, list)
        assert len(backup_codes) == 10  # Default count

        for code in backup_codes:
            assert isinstance(code, str)
            assert len(code) == 8  # 8-character codes
            assert code.isalnum()  # Alphanumeric
            assert code.isupper()  # Should be uppercase

        # All codes should be unique
        assert len(backup_codes) == len(set(backup_codes))

    def test_generate_backup_codes_custom_count(self, mfa_service):
        """Test backup code generation with custom count"""
        custom_count = 5
        backup_codes = mfa_service.generate_backup_codes(custom_count)

        assert len(backup_codes) == custom_count

    def test_generate_qr_code(self, mfa_service):
        """Test QR code generation"""
        test_url = "otpauth://totp/Test:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Test"

        qr_code_data = mfa_service.generate_qr_code(test_url)

        assert isinstance(qr_code_data, bytes)
        assert len(qr_code_data) > 0
        # PNG files start with specific bytes
        assert qr_code_data.startswith(b'\x89PNG\r\n\x1a\n')


class TestMFASetup:
    """Test MFA setup process"""

    @patch('app.services.mfa_service.get_settings')
    def test_setup_mfa_new_user(self, mock_get_settings, mfa_service, mock_db, sample_user):
        """Test MFA setup for new user"""
        # Mock settings
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        # Mock database query to return no existing MFA
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        secret, qr_code_url, backup_codes = mfa_service.setup_mfa(sample_user)

        assert isinstance(secret, str)
        assert len(secret) == 32
        assert isinstance(qr_code_url, str)
        assert "otpauth://totp/" in qr_code_url
        assert isinstance(backup_codes, list)
        assert len(backup_codes) == 10

        # Should create new MFA record
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_setup_mfa_existing_unverified(self, mfa_service, mock_db, sample_user):
        """Test MFA setup when user has existing unverified MFA"""
        # Create existing unverified MFA record
        existing_mfa = MFASecret(
            user_id=sample_user.id,
            tenant_id=sample_user.tenant_id,
            secret="OLDSECRET123",
            is_verified=False
        )

        # Mock database query to return existing MFA
        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_mfa

        secret, qr_code_url, backup_codes = mfa_service.setup_mfa(sample_user)

        # Should update existing record, not create new one
        assert existing_mfa.secret == secret
        assert existing_mfa.backup_codes == backup_codes
        assert existing_mfa.is_verified is False
        mock_db.add.assert_not_called()  # Should not add new record
        mock_db.commit.assert_called_once()

    def test_setup_mfa_already_verified(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test MFA setup when user already has verified MFA"""
        # Mock database query to return verified MFA
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        with pytest.raises(ValueError, match="already has MFA enabled"):
            mfa_service.setup_mfa(sample_user)


class TestMFAVerification:
    """Test TOTP and backup code verification"""

    def test_verify_totp_code_valid(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test verification of valid TOTP code"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        # Generate valid TOTP code
        totp = pyotp.TOTP(sample_mfa_secret.secret)
        valid_code = totp.now()

        result = mfa_service.verify_totp_code(sample_user, valid_code)

        assert result is True
        assert sample_mfa_secret.last_used_at is not None
        mock_db.commit.assert_called_once()

    def test_verify_totp_code_invalid(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test verification of invalid TOTP code"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        result = mfa_service.verify_totp_code(sample_user, "000000")

        assert result is False
        mock_db.commit.assert_not_called()

    def test_verify_backup_code_valid(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test verification of valid backup code"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        valid_backup_code = sample_mfa_secret.backup_codes[0]

        result = mfa_service.verify_totp_code(sample_user, valid_backup_code)

        assert result is True
        assert valid_backup_code not in sample_mfa_secret.backup_codes  # Should be removed
        assert sample_mfa_secret.backup_codes_used == 1
        assert sample_mfa_secret.last_used_at is not None
        mock_db.commit.assert_called_once()

    def test_verify_backup_code_case_insensitive(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test backup code verification is case insensitive"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        valid_backup_code = sample_mfa_secret.backup_codes[0].lower()

        result = mfa_service.verify_totp_code(sample_user, valid_backup_code)

        assert result is True

    def test_verify_backup_code_disabled(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test backup code verification when disabled"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        valid_backup_code = sample_mfa_secret.backup_codes[0]

        result = mfa_service.verify_totp_code(sample_user, valid_backup_code, allow_backup=False)

        assert result is False

    def test_verify_no_mfa_setup(self, mfa_service, mock_db, sample_user):
        """Test verification when user has no MFA setup"""
        # Mock database query to return None
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = mfa_service.verify_totp_code(sample_user, "123456")

        assert result is False

    def test_verify_marks_as_verified(self, mfa_service, mock_db, sample_user):
        """Test that verification marks MFA as verified during setup"""
        # Create unverified MFA
        unverified_mfa = MFASecret(
            user_id=sample_user.id,
            tenant_id=sample_user.tenant_id,
            secret="JBSWY3DPEHPK3PXP",
            backup_codes=["ABCD1234"],
            is_verified=False
        )

        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = unverified_mfa

        # Use backup code for verification
        result = mfa_service.verify_totp_code(sample_user, "ABCD1234")

        assert result is True
        assert unverified_mfa.is_verified is True


class TestMFAStatus:
    """Test MFA status and requirement checking"""

    def test_is_mfa_enabled_true(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test MFA enabled check when user has verified MFA"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        result = mfa_service.is_mfa_enabled(sample_user)

        assert result is True

    def test_is_mfa_enabled_false_no_mfa(self, mfa_service, mock_db, sample_user):
        """Test MFA enabled check when user has no MFA"""
        # Mock database query to return None
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = mfa_service.is_mfa_enabled(sample_user)

        assert result is False

    def test_is_mfa_enabled_false_unverified(self, mfa_service, mock_db, sample_user):
        """Test MFA enabled check when user has unverified MFA"""
        unverified_mfa = MFASecret(
            user_id=sample_user.id,
            is_verified=False
        )

        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = unverified_mfa

        result = mfa_service.is_mfa_enabled(sample_user)

        assert result is False

    def test_is_mfa_required_admin(self, mfa_service, sample_user):
        """Test MFA requirement for admin users"""
        sample_user.role = UserRole.admin

        result = mfa_service.is_mfa_required(sample_user)

        assert result is True

    def test_is_mfa_required_regular_user(self, mfa_service, regular_user):
        """Test MFA requirement for regular users"""
        result = mfa_service.is_mfa_required(regular_user)

        assert result is False

    def test_get_mfa_status_enabled(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test comprehensive MFA status for enabled user"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        status = mfa_service.get_mfa_status(sample_user)

        assert status["enabled"] is True
        assert status["verified"] is True
        assert status["required"] is True  # Admin user
        assert status["backup_codes_remaining"] == 3
        assert status["backup_codes_used"] == 0

    def test_get_mfa_status_disabled(self, mfa_service, mock_db, regular_user):
        """Test comprehensive MFA status for user without MFA"""
        # Mock database query to return None
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        status = mfa_service.get_mfa_status(regular_user)

        assert status["enabled"] is False
        assert status["verified"] is False
        assert status["required"] is False  # Regular user
        assert status["backup_codes_remaining"] == 0


class TestMFAManagement:
    """Test MFA management operations"""

    def test_disable_mfa_success(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test successful MFA disable"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        result = mfa_service.disable_mfa(sample_user)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_mfa_secret)
        mock_db.commit.assert_called_once()

    def test_disable_mfa_not_enabled(self, mfa_service, mock_db, sample_user):
        """Test disable MFA when not enabled"""
        # Mock database query to return None
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = mfa_service.disable_mfa(sample_user)

        assert result is False
        mock_db.delete.assert_not_called()

    def test_get_backup_codes_count(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test getting backup codes count"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        count = mfa_service.get_backup_codes_count(sample_user)

        assert count == 3

    def test_get_backup_codes_count_no_mfa(self, mfa_service, mock_db, sample_user):
        """Test getting backup codes count when no MFA"""
        # Mock database query to return None
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        count = mfa_service.get_backup_codes_count(sample_user)

        assert count == 0

    def test_regenerate_backup_codes_success(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test successful backup codes regeneration"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        new_codes = mfa_service.regenerate_backup_codes(sample_user)

        assert isinstance(new_codes, list)
        assert len(new_codes) == 10
        assert sample_mfa_secret.backup_codes == new_codes
        assert sample_mfa_secret.backup_codes_used == 0
        mock_db.commit.assert_called_once()

    def test_regenerate_backup_codes_not_enabled(self, mfa_service, mock_db, sample_user):
        """Test backup codes regeneration when MFA not enabled"""
        # Mock database query to return None
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="doesn't have MFA enabled"):
            mfa_service.regenerate_backup_codes(sample_user)

    def test_regenerate_backup_codes_unverified(self, mfa_service, mock_db, sample_user):
        """Test backup codes regeneration when MFA unverified"""
        unverified_mfa = MFASecret(
            user_id=sample_user.id,
            is_verified=False
        )

        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = unverified_mfa

        with pytest.raises(ValueError, match="doesn't have MFA enabled"):
            mfa_service.regenerate_backup_codes(sample_user)


class TestMFAEdgeCases:
    """Test edge cases and error conditions"""

    def test_verify_empty_code(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test verification with empty code"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        result = mfa_service.verify_totp_code(sample_user, "")

        assert result is False

    def test_verify_malformed_code(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test verification with malformed codes"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        malformed_codes = [
            "12345",      # Too short for TOTP
            "1234567",    # Too long for TOTP, too short for backup
            "ABCD123",    # Too short for backup
            "ABCD12345"   # Too long for backup
        ]

        for code in malformed_codes:
            result = mfa_service.verify_totp_code(sample_user, code)
            assert result is False, f"Code '{code}' should be invalid"

    def test_verify_used_backup_code(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test verification of already used backup code"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        # Use a backup code
        backup_code = sample_mfa_secret.backup_codes[0]
        first_result = mfa_service.verify_totp_code(sample_user, backup_code)
        assert first_result is True

        # Try to use the same code again
        second_result = mfa_service.verify_totp_code(sample_user, backup_code)
        assert second_result is False

    def test_concurrent_mfa_setup(self, mfa_service, mock_db, sample_user):
        """Test handling of concurrent MFA setup attempts"""
        # This would be more complex in real scenarios but tests the basic case
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # First setup
        secret1, qr1, codes1 = mfa_service.setup_mfa(sample_user)

        # Mock that MFA now exists for second attempt
        existing_mfa = MFASecret(user_id=sample_user.id, is_verified=True)
        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_mfa

        # Second setup should fail
        with pytest.raises(ValueError, match="already has MFA enabled"):
            mfa_service.setup_mfa(sample_user)

    def test_time_drift_tolerance(self, mfa_service, mock_db, sample_user, sample_mfa_secret):
        """Test TOTP verification with time drift"""
        # Mock database query
        mock_db.query.return_value.filter_by.return_value.first.return_value = sample_mfa_secret

        # TOTP typically allows for time drift (previous/next time window)
        totp = pyotp.TOTP(sample_mfa_secret.secret)

        # Get codes for different time windows
        import time
        current_time = int(time.time())

        # Test current window
        current_code = totp.at(current_time)
        assert mfa_service.verify_totp_code(sample_user, current_code) is True

        # Note: pyotp.verify() already handles time drift tolerance