"""
Helper Utilities Testleri (Task 6.2).

generate_request_code ve generate_unique_token fonksiyonlarının testleri.
"""
import pytest
import re
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.helpers import generate_request_code, generate_unique_token


# ===========================================================================
# generate_request_code Testleri
# ===========================================================================

class TestGenerateRequestCode:
    """generate_request_code fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_generate_request_code_format(self):
        """Request code #KAN-XXX formatında olmalı."""
        db_mock = AsyncMock(spec=AsyncSession)

        # Mock: Sequence'den ilk değer dönüyor
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 1
        db_mock.execute.return_value = result_mock

        code = await generate_request_code(db_mock)

        assert code == "#KAN-001"
        assert re.match(r"^#KAN-\d{3}$", code), "Format #KAN-XXX olmalı (3 digit)"

    @pytest.mark.asyncio
    async def test_generate_request_code_sequential(self):
        """Request code'lar ardışık olmalı."""
        db_mock = AsyncMock(spec=AsyncSession)

        # Mock: Sequence sıradaki değer olarak 6 döndürür
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 6
        db_mock.execute.return_value = result_mock

        code = await generate_request_code(db_mock)

        assert code == "#KAN-006", "Son kod 005 ise, sonraki 006 olmalı"

    @pytest.mark.asyncio
    async def test_generate_request_code_unique(self):
        """Her çağrıda farklı kod üretilmeli (sequence arttıkça)."""
        db_mock = AsyncMock(spec=AsyncSession)

        # İlk çağrı
        result_mock_1 = MagicMock()
        result_mock_1.scalar_one.return_value = 1

        # İkinci çağrı
        result_mock_2 = MagicMock()
        result_mock_2.scalar_one.return_value = 2

        db_mock.execute.side_effect = [result_mock_1, result_mock_2]

        code1 = await generate_request_code(db_mock)
        code2 = await generate_request_code(db_mock)

        assert code1 == "#KAN-001"
        assert code2 == "#KAN-002"
        assert code1 != code2

    @pytest.mark.asyncio
    async def test_generate_request_code_starts_from_one(self):
        """İlk request code #KAN-001 olmalı."""
        db_mock = AsyncMock(spec=AsyncSession)

        # Mock: Sequence ilk değer
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 1
        db_mock.execute.return_value = result_mock

        code = await generate_request_code(db_mock)

        assert code == "#KAN-001", "İlk kod 001'den başlamalı"

    @pytest.mark.asyncio
    async def test_generate_request_code_zero_padded(self):
        """Request code 3 digit zero-padded olmalı."""
        db_mock = AsyncMock(spec=AsyncSession)

        # Mock: Sequence 100 döndürüyor
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 100
        db_mock.execute.return_value = result_mock

        code = await generate_request_code(db_mock)

        assert code == "#KAN-100", "100 için zero-padding olmamalı"

    @pytest.mark.asyncio
    async def test_generate_request_code_large_number(self):
        """Büyük request sayılarında da çalışmalı."""
        db_mock = AsyncMock(spec=AsyncSession)

        # Mock: Sequence 1235 döndürüyor
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 1235
        db_mock.execute.return_value = result_mock

        code = await generate_request_code(db_mock)

        assert code == "#KAN-1235", "Büyük numaralar için 3 digit'ten fazla olmalı"

    @pytest.mark.asyncio
    async def test_generate_request_code_calls_database(self):
        """Database sorgusu yapılmalı (nextval sequence query)."""
        db_mock = AsyncMock(spec=AsyncSession)

        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 10
        db_mock.execute.return_value = result_mock

        await generate_request_code(db_mock)

        # execute çağrılmış olmalı
        db_mock.execute.assert_called_once()


# ===========================================================================
# generate_unique_token Testleri
# ===========================================================================

class TestGenerateUniqueToken:
    """generate_unique_token fonksiyonu testleri."""

    def test_generate_unique_token_length(self):
        """Token default length'te (32 byte) üretilmeli."""
        token = generate_unique_token()
        
        # token_urlsafe(32) yaklaşık 43 karakter üretir (base64 encoding)
        # 32 byte * 8 bit = 256 bit
        # 256 bit / 6 bit (base64) = ~43 karakter
        assert len(token) >= 32, "Token en az 32 karakter olmalı"
        assert isinstance(token, str)

    def test_generate_unique_token_uniqueness(self):
        """Her çağrıda farklı token üretilmeli."""
        token1 = generate_unique_token()
        token2 = generate_unique_token()
        token3 = generate_unique_token()
        
        assert token1 != token2
        assert token2 != token3
        assert token1 != token3
        assert len({token1, token2, token3}) == 3

    def test_generate_unique_token_default_length(self):
        """Default length 32 olmalı."""
        token = generate_unique_token()
        
        # Base64 encoding: 32 byte -> ~43 karakter
        assert 40 <= len(token) <= 50, "Default token uzunluğu ~43 karakter"

    def test_generate_unique_token_custom_length(self):
        """Custom length parametresi çalışmalı."""
        token_16 = generate_unique_token(16)
        token_64 = generate_unique_token(64)
        
        # 16 byte -> ~22 karakter
        # 64 byte -> ~86 karakter
        assert len(token_16) < len(token_64), "Daha uzun length daha uzun token üretmeli"
        assert 20 <= len(token_16) <= 30
        assert 80 <= len(token_64) <= 90

    def test_generate_unique_token_url_safe_characters(self):
        """Token yalnızca URL-safe karakterler içermeli."""
        token = generate_unique_token()
        
        # URL-safe base64: A-Z, a-z, 0-9, -, _
        url_safe_pattern = r"^[A-Za-z0-9_-]+$"
        assert re.match(url_safe_pattern, token), "Token URL-safe karakterler içermeli"

    def test_generate_unique_token_no_special_chars(self):
        """Token özel karakterler (+, /, =) içermemeli."""
        token = generate_unique_token()
        
        # URL-safe base64 bu karakterleri içermez
        assert "+" not in token
        assert "/" not in token
        assert "=" not in token

    def test_generate_unique_token_multiple_generations(self):
        """100 token üretildiğinde hepsi farklı olmalı."""
        tokens = [generate_unique_token() for _ in range(100)]
        unique_tokens = set(tokens)
        
        assert len(unique_tokens) == 100, "Tüm token'lar benzersiz olmalı"

    def test_generate_unique_token_minimum_length(self):
        """Minimum length (1) bile çalışmalı."""
        token = generate_unique_token(1)
        
        assert len(token) >= 1
        assert isinstance(token, str)

    def test_generate_unique_token_large_length(self):
        """Büyük length değerleri de çalışmalı."""
        token = generate_unique_token(256)
        
        # 256 byte -> ~342 karakter
        assert len(token) >= 256
        assert len(token) <= 400
