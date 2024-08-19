from pydantic import BaseModel


class LatestVersionBuild(BaseModel):
    build: int
    version: str

