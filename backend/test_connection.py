"""
test_connection.py
-------------------
A throwaway script — run this once to confirm your .env values are
correct and CognoDB is reachable.

Run with:  python test_connection.py   (from inside backend/, venv active)
"""

from app.db import get_session, verify_connection, close_driver

if __name__ == "__main__":
    print("Checking connectivity...")
    if not verify_connection():
        print("❌ Could not connect. Check your .env values.")
        exit(1)

    print("✅ Connected. Running a test query...")
    with get_session() as session:
        result = session.run("RETURN 1 AS test_value")
        record = result.single()
        print(f"✅ Query returned: {record['test_value']}")

    print("All good — CognoDB is reachable and responding.")
    close_driver()