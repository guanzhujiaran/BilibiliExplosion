from dataclasses import field, dataclass
from typing import Union

import numpy as np


@dataclass
class CaptchaInfo:
    img: np.ndarray
    position: list[int, int, int, int]  # x1,y1,x2,y2
    target_position: list[int] = field(default_factory=list)
    embeddings: np.ndarray = field(default_factory=list)


@dataclass
class CaptchaResultInfo:
    target_centers: Union[list[list[float]], None]
    img_name: str
    origin_img: np.ndarray = field(default_factory=list)
    bboxes: list[list[int]] = field(default_factory=list)


@dataclass
class GeetestRegInfo:
    type: str
    token: str
    geetest_challenge: str
    geetest_gt: str


@dataclass
class GeetestSuccessTimeCalc:
    succ_time: int = 0
    total_time: int = 0

    def calc_succ_rate(self):
        if self.total_time == 0:
            return 0
        return self.succ_time / self.total_time
