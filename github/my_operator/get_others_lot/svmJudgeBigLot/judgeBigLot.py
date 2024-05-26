# 使用joblib加载模型
# 或
import jieba
import joblib  # 对于新版sklearn
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from CONFIG import CONFIG

# 或者使用pickle加载模型
def preprocess_text(text):
    words = jieba.cut(text.strip())
    return ' '.join(words)

def big_lot_predict(da_list: list[str])->list[int]:
    if len(da_list)==0:
        return []
    relative_dir = 'github/my_operator/get_others_lot/svmJudgeBigLot/'
    with open(CONFIG.root_dir+relative_dir+'svm_model.pkl', 'rb') as file:
        loaded_model = pickle.load(file)
    with open(CONFIG.root_dir+relative_dir+'svm_vectorizer.pkl', 'rb') as file:
        loaded_vector = pickle.load(file)
    x_list=[]
    for i in da_list:
        # 预处理文本
        processed_text = preprocess_text(i)
        print(processed_text)
        x_list.append(processed_text)
    x = loaded_vector.transform(x_list)
    predictions = loaded_model.predict(x)

    return predictions


if __name__ == '__main__':
    rest = big_lot_predict(
        [
            """《明日方舟》五周年生日快乐！🎉🎉🎉 

◆关注并转发本条动态，我们将抽取20位博士每人赠送【阿米娅 庆典时光手办】一份。"""

        ]
    )
    print(rest)

