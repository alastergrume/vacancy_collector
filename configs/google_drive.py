from pydantic_settings import SettingsConfigDict

from configs.base import EnvSettings


class GoogleDriveSettings(EnvSettings):
    """Google Диск: OAuth-клиент (тип «Веб-приложение») из Google Cloud Console."""

    model_config = SettingsConfigDict(env_prefix="GDRIVE_")

    client_id: str = ""
    client_secret: str = ""
    # ID папки на Диске, куда выгружать таблицу (из адреса папки)
    folder_id: str = ""
    export_file_name: str = "hh_вакансии.xlsx"
    scopes: str = "https://www.googleapis.com/auth/drive.file"

    @property
    def scope_list(self) -> list[str]:
        return [s.strip() for s in self.scopes.split(",") if s.strip()]

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)
