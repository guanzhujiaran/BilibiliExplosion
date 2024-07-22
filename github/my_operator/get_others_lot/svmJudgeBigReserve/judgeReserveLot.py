# 使用joblib加载模型
# 或
import os

import jieba
import joblib  # 对于新版sklearn
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from CONFIG import CONFIG


# 或者使用pickle加载模型
def preprocess_text(text):
    text.replace('预约有奖：', '')
    words = jieba.cut(text.strip())
    return ' '.join(words)


def big_reserve_predict(da_list: list[str]) -> list[int]:
    if len(da_list) == 0:
        return []
    current_file_dir = os.path.dirname(__file__)
    with open(os.path.join(current_file_dir, 'svm_model.pkl'), 'rb') as file:
        loaded_model = pickle.load(file)
    with open(os.path.join(current_file_dir, 'svm_vectorizer.pkl'), 'rb') as file:
        loaded_vector = pickle.load(file)
    X_list = []
    for i in da_list:
        X_list.append(preprocess_text(i))
    X = loaded_vector.transform(X_list)
    predictions = loaded_model.predict(X)

    return predictions


if __name__ == '__main__':
    rest = big_reserve_predict(
        [
            '星极破冰1000W电源*1份、冰心360水冷*1份、琥珀海景房机箱*1份、耕升周边*5份',
            '预约有奖：随机隐藏款手办一份*1份',
            '预约有奖：万代随机景品一个*1份',
            '预约有奖：肩颈按摩仪*1份'
        ]
    )
    print(rest)
    print(len(rest))
