import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "LessonFoundry"
    API_V1_STR: str = "/api/v1"
    
    # LLM Provider Configuration ('groq' or 'gemini')
    LLM_PROVIDER: str = "groq"

    # Groq Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Gemini Configuration
    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    AUTH_SECRET_KEY: str = "lessonfoundry-oauth-secret-key-yuva-2026"
    
    # Database
    SQLITE_DB_PATH: str = str(BASE_DIR / "lessonfoundry.db")
    
    model_config = SettingsConfigDict(
        env_file=[str(BASE_DIR / ".env"), str(BASE_DIR / "backend" / ".env")],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

def get_effective_gemini_api_key() -> str:
    """Returns GEMINI_API_KEY or GOOGLE_API_KEY from fresh .env, settings, or os.environ."""
    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                key = vals.get("GEMINI_API_KEY") or vals.get("GOOGLE_API_KEY")
                if key and key.strip():
                    return key.strip().strip("'\"")
    except Exception:
        pass

    raw_key = (
        os.environ.get("GEMINI_API_KEY", "")
        or os.environ.get("GOOGLE_API_KEY", "")
        or settings.GEMINI_API_KEY
        or settings.GOOGLE_API_KEY
    )
    return raw_key.strip().strip("'\"")

def get_effective_gemini_model() -> str:
    """Returns GEMINI_MODEL from fresh .env, settings, or os.environ."""
    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                model = vals.get("GEMINI_MODEL")
                if model and model.strip():
                    return model.strip().strip("'\"")
    except Exception:
        pass

    return (
        os.environ.get("GEMINI_MODEL", "")
        or settings.GEMINI_MODEL
        or "gemini-3.8-flash"
    ).strip().strip("'\"")

def get_effective_llm_provider() -> str:
    """Returns LLM_PROVIDER ('groq' or 'gemini') from os.environ, fresh .env, or settings."""
    env_provider = os.environ.get("LLM_PROVIDER", "").strip().strip("'\"").lower()
    if env_provider:
        return env_provider

    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                provider = vals.get("LLM_PROVIDER")
                if provider and provider.strip():
                    return provider.strip().strip("'\"").lower()
    except Exception:
        pass
    return (settings.LLM_PROVIDER or "groq").strip().strip("'\"").lower()

def get_effective_groq_api_key() -> str:
    """Returns GROQ_API_KEY from os.environ, fresh .env, or settings."""
    env_key = os.environ.get("GROQ_API_KEY", "").strip().strip("'\"")
    if env_key and env_key != "<MY_GROQ_API_KEY>":
        return env_key

    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                key = vals.get("GROQ_API_KEY")
                if key and key.strip() and key.strip().strip("'\"") != "<MY_GROQ_API_KEY>":
                    return key.strip().strip("'\"")
    except Exception:
        pass

    raw_key = settings.GROQ_API_KEY
    return raw_key.strip().strip("'\"")

def get_effective_groq_model() -> str:
    """Returns GROQ_MODEL from os.environ, fresh .env, or settings."""
    env_model = os.environ.get("GROQ_MODEL", "").strip().strip("'\"")
    if env_model:
        return env_model

    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                model = vals.get("GROQ_MODEL")
                if model and model.strip():
                    return model.strip().strip("'\"")
    except Exception:
        pass

    return (settings.GROQ_MODEL or "openai/gpt-oss-20b").strip().strip("'\"")

def get_effective_groq_base_url() -> str:
    """Returns GROQ_BASE_URL from os.environ, fresh .env, or settings."""
    env_url = os.environ.get("GROQ_BASE_URL", "").strip().strip("'\"")
    if env_url:
        return env_url

    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                url = vals.get("GROQ_BASE_URL")
                if url and url.strip():
                    return url.strip().strip("'\"")
    except Exception:
        pass

    return (settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1").strip().strip("'\"")

def get_effective_google_client_id() -> str:
    """Returns GOOGLE_CLIENT_ID from os.environ, fresh .env, or settings."""
    env_val = os.environ.get("GOOGLE_CLIENT_ID", "").strip().strip("'\"")
    if env_val:
        return env_val

    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                val = vals.get("GOOGLE_CLIENT_ID")
                if val and val.strip():
                    return val.strip().strip("'\"")
    except Exception:
        pass

    return (settings.GOOGLE_CLIENT_ID or "").strip().strip("'\"")

def get_effective_google_client_secret() -> str:
    """Returns GOOGLE_CLIENT_SECRET from os.environ, fresh .env, or settings."""
    env_val = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip().strip("'\"")
    if env_val:
        return env_val

    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                val = vals.get("GOOGLE_CLIENT_SECRET")
                if val and val.strip():
                    return val.strip().strip("'\"")
    except Exception:
        pass

    return (settings.GOOGLE_CLIENT_SECRET or "").strip().strip("'\"")

def get_effective_google_redirect_uri() -> str:
    """Returns GOOGLE_REDIRECT_URI from os.environ, fresh .env, or settings."""
    env_val = os.environ.get("GOOGLE_REDIRECT_URI", "").strip().strip("'\"")
    if env_val:
        return env_val

    try:
        from dotenv import dotenv_values
        for env_file in [BASE_DIR / ".env", BASE_DIR / "backend" / ".env"]:
            if env_file.exists():
                vals = dotenv_values(env_file)
                val = vals.get("GOOGLE_REDIRECT_URI")
                if val and val.strip():
                    return val.strip().strip("'\"")
    except Exception:
        pass

    return (settings.GOOGLE_REDIRECT_URI or "http://localhost:8000/api/v1/auth/google/callback").strip().strip("'\"")

def is_google_oauth_configured() -> bool:
    """Returns True if Google OAuth is configured with non-placeholder credentials."""
    client_id = get_effective_google_client_id()
    client_secret = get_effective_google_client_secret()
    
    if not client_id or not client_secret:
        return False
    # Check for placeholder strings
    placeholders = ["your_google_client_id_here", "your-client-id", "placeholder", "xxx"]
    if any(p in client_id.lower() for p in placeholders):
        return False
    if any(p in client_secret.lower() for p in placeholders):
        return False
    return len(client_id) >= 10 and len(client_secret) >= 10


