from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class LatestVersionBuild(CustomBaseModel):
    build: int # "890110"
    version: str  # "8.9.0"

