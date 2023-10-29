import re

from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

semantic_cls = pipeline(Tasks.text_classification, 'damo/nlp_structbert_sentiment-classification_chinese-large')


def judge_semantic_cls(input_str):
    res = semantic_cls(
        input=re.sub('\[.{0,15}]', '', input_str),
    )
    print(input_str, res)
    return True if res.get('labels')[0] == '正面' else False


if __name__ == '__main__':
    judge_semantic_cls('很满意，音质很好，发货速度快，值得购买')
