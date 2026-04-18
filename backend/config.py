from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcs_bucket_name: str = "revisor-margens-inovatta"
    gcp_project_id: str = "inovatta-revisor-margens"
    signed_url_expiry_hours: int = 1

    class Config:
        env_file = ".env"


settings = Settings()
