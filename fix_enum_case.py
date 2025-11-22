"""
Fix RecordType enum to use uppercase LEAD instead of Lead
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def fix_enum():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")

    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(DATABASE_URL)

    try:
        async with engine.begin() as conn:
            # Check current values
            result = await conn.execute(
                text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'recordtype' ORDER BY e.enumsortorder")
            )
            current_values = [row[0] for row in result.fetchall()]

            print("Current enum values:")
            for val in current_values:
                print(f"  - '{val}'")

            # Check if LEAD exists
            if "LEAD" in current_values:
                print("\n✅ 'LEAD' already exists. No migration needed.")
                return

            # Add LEAD
            print("\nAdding 'LEAD' to enum...")
            await conn.execute(text("ALTER TYPE recordtype ADD VALUE 'LEAD'"))
            print("✅ Added 'LEAD' to enum")

            # Note: We cannot remove enum values in PostgreSQL without recreating the type
            # So we'll keep both 'Lead' and 'LEAD', but Python will only use 'LEAD'
            if "Lead" in current_values:
                print("\n⚠️ Note: 'Lead' (title case) still exists in database")
                print("   This is OK - Python will use 'LEAD' and ignore 'Lead'")

            # Verify
            result = await conn.execute(
                text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'recordtype' ORDER BY e.enumsortorder")
            )
            new_values = [row[0] for row in result.fetchall()]

            print("\nFinal enum values:")
            for val in new_values:
                marker = "✓" if val in ["ACCOUNT", "CONTACT", "LEAD"] else " "
                print(f"  {marker} '{val}'")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("="*80)
    print("FIX ENUM: Add uppercase 'LEAD' to recordtype")
    print("="*80 + "\n")
    asyncio.run(fix_enum())
    print("\n" + "="*80)
    print("Migration complete!")
    print("="*80)
