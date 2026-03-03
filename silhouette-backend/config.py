from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # LLM
    groq_api_key:    str  = ""
    ollama_base_url: str  = "http://localhost:11434"
    ollama_model:    str  = "llama3.2"

    # LangSmith
    langchain_tracing_v2: str = "false"
    langchain_api_key:    str = ""
    langchain_project:    str = "silhouette"

    # Paths
    image_store_path:    str = "./image_store"
    chroma_path:         str = "./data/chroma"
    knowledge_base_path: str = "./knowledge_base"

    # Routing
    fast_llm:  str = "groq"    # groq for speed (text-only tasks)
    smart_llm: str = "ollama" 

    class Config:
        env_file = ".env"
        extra = "ignore"

    def ensure_dirs(self):
        for path in [self.image_store_path, self.chroma_path, self.knowledge_base_path]:
            Path(path).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
