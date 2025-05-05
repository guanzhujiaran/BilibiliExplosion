import asyncio
import re
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from fastapi接口.log.base_log import myfastapi_logger
_lock = asyncio.Lock()

class DamoSemantic:
    _semantic_cls = None

    async def semantic(self,input_str: str) -> bool:
        if self._semantic_cls is None:
            async with _lock:
                if self._semantic_cls is None:
                    try:
                        self._semantic_cls = await asyncio.to_thread(
                            pipeline, task=Tasks.text_classification,
                            model='iic/nlp_structbert_sentiment-classification_chinese-base',
                        )
                    except Exception as e:
                        myfastapi_logger.exception(f"semantic_cls error: {e}")
                        return True
        res = await asyncio.to_thread(self._semantic_cls, input=re.sub('\[.{0,15}]', '', input_str), )
        return True if res.get('labels')[0] == '正面' else False

damo_semantic = DamoSemantic()

