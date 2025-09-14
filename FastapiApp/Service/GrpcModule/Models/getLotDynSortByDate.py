from pydantic import Field
from CONFIG import CONFIG

from Models.base.custom_pydantic import CustomBaseModel
import os


def _get_zip_path():
    return os.path.join(CONFIG.root_dir, 'scripts/database/dyn_backup')


class MainConf(CustomBaseModel):
    between_ts: list[int] | None = None
    is_gen_word_cloud: bool = False
    is_gen_zip: bool = False
    gen_zip_path: str = Field(default_factory=_get_zip_path)
    is_delete_generated_data: bool = False
