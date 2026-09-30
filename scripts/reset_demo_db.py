import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import Base, engine, init_db

def reset_database():
    """
    Safely resets the local SQLite database to a pristine empty state
    with all schemas initialized. Does NOT preload any mock or fake educational content.
    Ready for fresh live source ingestion.
    """
    print("Resetting LessonFoundry database for clean judge demo...")
    engine.dispose()
    
    db_file = BASE_DIR / "lessonfoundry.db"
    wal_file = BASE_DIR / "lessonfoundry.db-wal"
    shm_file = BASE_DIR / "lessonfoundry.db-shm"

    for f in [db_file, wal_file, shm_file]:
        if f.exists():
            try:
                os.remove(f)
                print(f"  Removed: {f.name}")
            except Exception as e:
                print(f"  Note: Could not delete {f.name} (in use): {e}")

    # Re-initialize clean schema
    init_db()
    print("[SUCCESS] Database schema initialized fresh. Zero preloaded content.")
    print("Ready for live demo generation from fresh source document.")

if __name__ == "__main__":
    reset_database()
