from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    service_name: str = "Secure RAG Support Assistant"
    app_env: str = "development"
    log_level: str = "INFO"
    enable_llm: bool = False
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    api_auth_enabled: bool = True
    api_auth_token: str = "demo-support-token"
    knowledge_base_dir: Path = Path("knowledge_base")
    vector_store_path: Path = Path("chroma_db")
    mock_data_dir: Path = Path("data/mock")
    collection_name: str = "support_kb"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = 4
    min_confidence: float = 0.45

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def openai_enabled(self) -> bool:
        token = (self.openai_api_key or "").strip().lower()
        is_dummy_token = token.startswith("dummy") or token.startswith("change-me") or token.startswith("your-")
        return self.enable_llm and bool(token) and not is_dummy_token


def _resolve_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.knowledge_base_dir = _resolve_project_path(settings.knowledge_base_dir)
    settings.vector_store_path = _resolve_project_path(settings.vector_store_path)
    settings.mock_data_dir = _resolve_project_path(settings.mock_data_dir)
    settings.vector_store_path.mkdir(parents=True, exist_ok=True)
    return settings

