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
    X_list=[]
    for i in da_list:
        X_list.append(preprocess_text(i))
    X = loaded_vector.transform(X_list)
    predictions = loaded_model.predict(X)

    return predictions


if __name__ == '__main__':
    rest = big_lot_predict(
        [
            '春分已至，万象耕新。天气渐暖，红缨来为小伙伴们送上福利啦~记得【关注@耕升Gainward +转发评论此动态】参与抽奖哦[星星眼]\n活动时间：2024.3.21-2024.4.15，祝大家今年都有好运气！\n\n【活动奖品】\n一等奖：星极破冰1000W电源*1\n二等奖：冰心360水冷*1\n三等奖：琥珀海景房机箱*1\n四等奖：耕升周边*5 \n\n大伙儿快快参与吧！！#抽奖动态##互动抽奖#',
            '星极破冰1000W电源*1份、冰心360水冷*1份、琥珀海景房机箱*1份、耕升周边*5份',
            '预约有奖：随机隐藏款手办一份*1份',
            '预约有奖：万代随机景品一个*1份',
            '预约有奖：肩颈按摩仪*1份'

        ]
    )
    print(rest)

