# 使用joblib加载模型
# 或
import asyncio
import os

import jieba3
import pickle

current_file_dir = os.path.dirname(__file__)
with open(os.path.join(current_file_dir, 'svm_model.pkl'), 'rb') as file:
    loaded_model = pickle.load(file)
with open(os.path.join(current_file_dir, 'svm_vectorizer.pkl'), 'rb') as file:
    loaded_vector = pickle.load(file)
# 或者使用pickle加载模型
tokenizer = jieba3.jieba3(model="small")

def preprocess_text(text):
    text.replace('预约有奖：', '')
    try:
        words = tokenizer.cut_text(text.strip())
        return ' '.join(words)
    except Exception as e:
        return text

def _big_reserve_predict_sync(da_list: list[str]) -> list[int]:
    """SVM 大奖判断的同步实现"""
    if not da_list:
        return []
    X_list = [preprocess_text(i) for i in da_list]
    X = loaded_vector.transform(X_list)
    return loaded_model.predict(X)

async def big_reserve_predict(da_list: list[str]) -> list[int]:
    """异步执行 SVM 大奖判断（在线程池中运行以避免阻塞事件循环）"""
    return await asyncio.to_thread(_big_reserve_predict_sync, da_list)


if __name__ == '__main__':
    rest = asyncio.run(big_reserve_predict(
        [
            '星极破冰1000W电源*1份、冰心360水冷*1份、琥珀海景房机箱*1份、耕升周边*5份',
            '预约有奖：随机隐藏款手办一份*1份',
            '预约有奖：万代随机景品一个*1份',
            '预约有奖：肩颈按摩仪*1份'
        ]
    ))
    print(rest)
    print(len(rest))
