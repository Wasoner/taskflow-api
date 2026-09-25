"""Configuración central de la aplicación.

Todos los valores sensibles (credenciales, URLs) se leen del archivo .env,
nunca están escritos en el código. Así se cumple el principio de menor
privilegio y se evita filtrar secretos al subir el código a Git.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "TaskFlow API"
    app_version: str = "1.0.0"
    database_url: str
    mongo_url: str


settings = Settings()
