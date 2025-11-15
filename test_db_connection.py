"""
Quick test to verify database connection
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")
    print(f"Testing connection to: {DATABASE_URL[:30]}...")

    try:
        import asyncpg

        # Convert to asyncpg format
        if DATABASE_URL.startswith("postgresql://"):
            url = DATABASE_URL
        else:
            url = DATABASE_URL

        # Test connection
        conn = await asyncpg.connect(url)
        print("✅ Successfully connected to PostgreSQL!")

        # Test query
        version = await conn.fetchval('SELECT version()')
        print(f"Database version: {version[:50]}...")

        await conn.close()
        print("✅ Connection test successful!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
