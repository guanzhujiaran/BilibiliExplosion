import asyncio
import re
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

class DamoSemantic:
    _semantic_cls = pipeline(task=Tasks.text_classification,model='iic/nlp_structbert_sentiment-classification_chinese-base')

    async def semantic(self,input_str: str) -> bool:
        res = await asyncio.to_thread(self._semantic_cls, input=re.sub('\[.{0,15}]', '', input_str), )
        return True if res.get('labels')[0] == '正面' else False

damo_semantic = DamoSemantic()

