"""
Migration: Add 'Lead' to recordtype enum

This script adds the 'Lead' value to the existing PostgreSQL enum type 'recordtype'
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    """Add Lead to recordtype enum"""

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Convert to async URL
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(DATABASE_URL)

    try:
        async with engine.begin() as conn:
            print("Checking if 'Lead' value already exists in recordtype enum...")

            # Check if Lead already exists
            result = await conn.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'recordtype' AND e.enumlabel = 'Lead')")
            )
            row = result.fetchone()
            exists = row[0] if row else False

            if exists:
                print("✅ 'Lead' value already exists in recordtype enum. No migration needed.")
            else:
                print("Adding 'Lead' to recordtype enum...")

                # Add Lead to the enum
                await conn.execute(text("ALTER TYPE recordtype ADD VALUE 'Lead'"))

                print("✅ Successfully added 'Lead' to recordtype enum!")

        print("\nMigration complete!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("="*80)
    print("DATABASE MIGRATION: Add 'Lead' to recordtype enum")
    print("="*80 + "\n")

    asyncio.run(migrate())
