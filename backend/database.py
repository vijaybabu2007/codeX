from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

DATABASE_URL = f"sqlite:///{settings.SQLITE_DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Enable SQLite Write-Ahead Logging (WAL) mode and Foreign Key enforcement
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    import backend.models # Ensure models are loaded
    Base.metadata.create_all(bind=engine)
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(quiz_question_versions);")).fetchall()
            cols = [r[1] for r in result]
            if cols:
                if "teacher_notes" not in cols:
                    conn.execute(text("ALTER TABLE quiz_question_versions ADD COLUMN teacher_notes TEXT;"))
                if "rationale" not in cols:
                    conn.execute(text("ALTER TABLE quiz_question_versions ADD COLUMN rationale TEXT;"))
                conn.commit()
            pack_result = conn.execute(text("PRAGMA table_info(learning_packs);")).fetchall()
            pack_cols = [r[1] for r in pack_result]
            if pack_cols and "owner_id" not in pack_cols:
                conn.execute(text("ALTER TABLE learning_packs ADD COLUMN owner_id TEXT;"))
                conn.commit()
            user_result = conn.execute(text("PRAGMA table_info(users);")).fetchall()
            user_cols = [r[1] for r in user_result]
            if user_cols and "student_id" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN student_id TEXT;"))
                conn.commit()
    except Exception:
        pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
