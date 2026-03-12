"""
Telefon numarası normalizasyon unit test'leri.

Bu test dosyası, normalize_phone fonksiyonunun çeşitli input formatlarını
doğru şekilde işlediğini doğrular.
"""
import pytest

from app.utils.helpers import normalize_phone


class TestPhoneNormalization:
    """Telefon numarası normalizasyon test sınıfı."""

    def test_plus90_prefix_unchanged(self):
        """+90555... formatı değişmeden kalmalı."""
        assert normalize_phone("+905551234567") == "+905551234567"

    def test_0_prefix_conversion(self):
        """0555... formatı +90555... olmalı."""
        assert normalize_phone("05551234567") == "+905551234567"

    def test_no_prefix_conversion(self):
        """555... formatı +90555... olmalı."""
        assert normalize_phone("5551234567") == "+905551234567"

    def test_90_prefix_conversion(self):
        """BUG FIX: 90555... -> +90555... (not +9090555...)."""
        assert normalize_phone("905551234567") == "+905551234567"

    def test_with_spaces(self):
        """Boşluklu numara temizlenmeli ve normalize edilmeli."""
        assert normalize_phone("0555 123 45 67") == "+905551234567"

    def test_90_prefix_with_spaces(self):
        """90555 format with spaces -> +90555..."""
        assert normalize_phone("90 555 123 45 67") == "+905551234567"

    def test_plus90_with_spaces(self):
        """+90 ile başlayan ve boşluklu numara düzgün çalışmalı."""
        assert normalize_phone("+90 555 123 45 67") == "+905551234567"

    def test_only_digits_no_prefix(self):
        """Sadece rakamlar (önek yok) -> +90 eklenmeli."""
        assert normalize_phone("5551234567") == "+905551234567"

    def test_various_turkish_phone_numbers(self):
        """Farklı Türk telefon numaraları doğru normalize edilmeli."""
        test_cases = [
            ("+905321234567", "+905321234567"),
            ("05321234567", "+905321234567"),
            ("5321234567", "+905321234567"),
            ("905321234567", "+905321234567"),
            ("+905441234567", "+905441234567"),
            ("05441234567", "+905441234567"),
            ("5441234567", "+905441234567"),
            ("905441234567", "+905441234567"),
        ]
        for input_phone, expected in test_cases:
            assert normalize_phone(input_phone) == expected, f"Failed for: {input_phone}"

    def test_strip_whitespace(self):
        """Başındaki ve sonundaki boşluklar temizlenmeli."""
        assert normalize_phone("  05551234567  ") == "+905551234567"
        assert normalize_phone("\t905551234567\n") == "+905551234567"

    def test_edge_case_double_zero(self):
        """00 ile başlayan numara (geçersiz format ama fonksiyon tutarlı çalışmalı)."""
        # 0090555... -> +90090555... (0 ile başlıyor -> +90 eklenir)
        assert normalize_phone("00905551234567") == "+900905551234567"
