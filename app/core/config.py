from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    retrieval_top_k: int = 3
    context_token_budget: int = 2000
    docs_dir: str = "app/data/docs"


settings = Settings()
