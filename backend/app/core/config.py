from pathlib import Path
from functools import lru_cache
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    data_dir: Path = Field(default=Path('data'), validation_alias=AliasChoices('CLINICALRAG_DATA_DIR','DATA_DIR'))
    database_url: str = Field(default='sqlite:///./data/clinicalrag.db', validation_alias=AliasChoices('CLINICALRAG_DATABASE_URL','DATABASE_URL'))
    llm_provider: str = Field(default='retrieval_only', validation_alias=AliasChoices('CLINICALRAG_LLM_PROVIDER','LLM_PROVIDER'))
    openai_compatible_base_url: str | None = Field(default=None, validation_alias=AliasChoices('CLINICALRAG_OPENAI_COMPATIBLE_BASE_URL','OPENAI_COMPATIBLE_BASE_URL'))
    openai_compatible_api_key: str | None = Field(default=None, validation_alias=AliasChoices('CLINICALRAG_OPENAI_COMPATIBLE_API_KEY','OPENAI_COMPATIBLE_API_KEY'))
    openai_compatible_model: str = Field(default='gpt-4o-mini', validation_alias=AliasChoices('CLINICALRAG_OPENAI_COMPATIBLE_MODEL','OPENAI_COMPATIBLE_MODEL'))
    ollama_base_url: str = Field(default='http://localhost:11434', validation_alias=AliasChoices('CLINICALRAG_OLLAMA_BASE_URL','OLLAMA_BASE_URL'))
    ollama_model: str = Field(default='llama3.1', validation_alias=AliasChoices('CLINICALRAG_OLLAMA_MODEL','OLLAMA_MODEL'))
    embedding_provider: str = Field(default='local_hash', validation_alias=AliasChoices('CLINICALRAG_EMBEDDING_PROVIDER','EMBEDDING_PROVIDER'))
    embedding_dim: int = Field(default=384, validation_alias=AliasChoices('CLINICALRAG_EMBEDDING_DIM','EMBEDDING_DIM'))
    vector_store: str = Field(default='local', validation_alias=AliasChoices('CLINICALRAG_VECTOR_STORE','VECTOR_STORE'))
    top_k: int = Field(default=6, validation_alias=AliasChoices('CLINICALRAG_TOP_K','TOP_K'))
    chunk_size: int = Field(default=900, validation_alias=AliasChoices('CLINICALRAG_CHUNK_SIZE','CHUNK_SIZE'))
    chunk_overlap: int = Field(default=160, validation_alias=AliasChoices('CLINICALRAG_CHUNK_OVERLAP','CHUNK_OVERLAP'))
    cors_origins_csv: str = Field(default='http://localhost:3000,http://127.0.0.1:3000', validation_alias=AliasChoices('CLINICALRAG_CORS_ORIGINS','CORS_ORIGINS'))
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', populate_by_name=True)
    @property
    def cors_origins(self): return [x.strip() for x in self.cors_origins_csv.split(',') if x.strip()]
    @property
    def raw_dir(self): return self.data_dir/'demo_corpus'/'raw'
    @property
    def indexes_dir(self): return self.data_dir/'indexes'
    def ensure_dirs(self):
        for p in [self.data_dir, self.raw_dir, self.indexes_dir, self.data_dir/'processed']:
            p.mkdir(parents=True, exist_ok=True)
@lru_cache
def get_settings():
    s=Settings(); s.ensure_dirs(); return s
settings=get_settings()
