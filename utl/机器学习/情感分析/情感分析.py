import json
import re
import time
import traceback
import redis

r1 = redis.Redis(host='localhost', port=11451, db=1)
try:
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks
    from loguru import logger

    semantic_cls = pipeline(Tasks.text_classification,
                            'damo/nlp_structbert_sentiment-classification_chinese-large', )
except Exception as e:
    traceback.print_exc()
    semantic_cls = None


def judge_semantic_cls(input_str):
    if not semantic_cls:
        return True
    res = semantic_cls(
        input=re.sub('\[.{0,15}]', '', input_str),
    )
    logger.info('%s: %s' % (input_str, res))
    return True if res.get('labels')[0] == '正面' else False


def get_input_str_from_redis():
    for k in r1.keys():
        da = r1.get(k)
        if da:
            res = json.loads(da).get(k.decode('utf-8'))
            if res is None:
                r1.setex(k, 180, json.dumps({k.decode('utf-8'): judge_semantic_cls(k.decode('utf-8'))}))


if __name__ == '__main__':
    while 1:
        get_input_str_from_redis()
        time.sleep(5)
