from enum import Enum

import cv2

class PicPreprocessType(str, Enum):
    NonProcess = "NonProcess"



class PlugPicPreprocess:
    
    @staticmethod
    def non_process(src: cv2.typing.MatLike,*args,**kwargs) -> cv2.typing.MatLike:
        return src

    @staticmethod
    def pic_preprocess_gen(pic_preprocess_type:PicPreprocessType):
        if pic_preprocess_type == PicPreprocessType.NonProcess:
            return PlugPicPreprocess.non_process
        else:
            return PlugPicPreprocess.non_process

