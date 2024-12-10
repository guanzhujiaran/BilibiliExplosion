import asyncio
import re
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from fastapi接口.log.base_log import myfastapi_logger

_lock = asyncio.Lock()

semantic_cls = None


async def semantic(input_str: str) -> bool:
    global semantic_cls
    async with _lock:
        if semantic_cls is None:
            try:
                semantic_cls = await asyncio.to_thread(
                    pipeline, task=Tasks.text_classification,
                    model='damo/nlp_structbert_sentiment-classification_chinese-large',
                )
            except Exception as e:
                myfastapi_logger.exception(f"semantic_cls error: {e}")
                return True
    res = await asyncio.to_thread(semantic_cls, input=re.sub('\[.{0,15}]', '', input_str), )
    return True if res.get('labels')[0] == '正面' else False

if __name__ == "__main__":
    print(asyncio.run(semantic("你好")))