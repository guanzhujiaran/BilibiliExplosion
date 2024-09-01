from pydantic import BaseModel


class LatestVersionBuild(BaseModel):
    build: int # "890110"
    version: str  # "8.9.0"

