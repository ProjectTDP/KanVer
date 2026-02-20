#!/usr/bin/env python3
"""
KanVer Database Cleanup Script

Tüm tabloları temizler.
DİKKAT: Tüm verileri siler!

Not: UUID kullanıyoruz, sequence reset'e gerek yok.

Kullanım:
    python -m scripts.cleanup_db
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import AsyncSessionLocal


# FK bağımlılık sırasına göre (child → parent)
TABLES_TO_TRUNCATE = [
    "notifications",         # Her şeyin child'ı
    "donations",             # qr_code, commitment, blood_request child'ı
    "qr_codes",              # commitment child'ı
    "donation_commitments",  # user, blood_request child'ı
    "blood_requests",        # requester, hospital child'ı
    "hospital_staff",        # user, hospital child'ı
    "hospitals",             # Parent
    "users",                 # Parent
]


async def cleanup_database():
    """Tüm tabloları temizle."""
    print("🧹 KanVer Database Cleanup")
    print("=" * 40)
    print("⚠️  TÜM VERİLER SİLİNECEK!")
    print()

    # İki kez onay iste
    confirm = input("Devam etmek için 'evet' yazın: ")
    if confirm.lower() != "evet":
        print("İptal edildi.")
        return

    confirm2 = input("Emin misiniz? Tüm veriler silinecek (tekrar 'evet'): ")
    if confirm2.lower() != "evet":
        print("İptal edildi.")
        return

    async with AsyncSessionLocal() as session:
        try:
            # CASCADE ile truncate (FK constraints'i otomatik handle eder)
            for table in TABLES_TO_TRUNCATE:
                await session.execute(
                    text(f'TRUNCATE TABLE "{table}" CASCADE')
                )
                print(f"✅ {table} temizlendi")

            await session.commit()
            print("\n🎉 Database temizlendi!")
            print("📝 Not: UUID kullanıyoruz, sequence reset gerekmiyor.")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Hata: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


async def show_counts():
    """Mevcut kayıt sayılarını göster."""
    print("📊 Mevcut Kayıt Sayıları:")
    print("-" * 30)

    async with AsyncSessionLocal() as session:
        for table in TABLES_TO_TRUNCATE:
            try:
                result = await session.execute(
                    text(f'SELECT COUNT(*) FROM "{table}"')
                )
                count = result.scalar()
                print(f"  {table}: {count}")
            except Exception as e:
                print(f"  {table}: Hata - {e}")


async def main():
    """Ana fonksiyon."""
    import argparse

    parser = argparse.ArgumentParser(description="KanVer Database Cleanup")
    parser.add_argument("--count", action="store_true", help="Sadece kayıt sayılarını göster")
    args = parser.parse_args()

    if args.count:
        await show_counts()
    else:
        await cleanup_database()


if __name__ == "__main__":
    asyncio.run(main())
