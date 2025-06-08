# 使用joblib加载模型
# 或
import os
import jieba
import pickle

current_file_dir = os.path.dirname(__file__)
with open(os.path.join(current_file_dir, 'svm_model.pkl'), 'rb') as file:
    loaded_model = pickle.load(file)
with open(os.path.join(current_file_dir, 'svm_vectorizer.pkl'), 'rb') as file:
    loaded_vector = pickle.load(file)
# 或者使用pickle加载模型
def preprocess_text(text):
    try:
        words = jieba.cut(text.strip())
        return ' '.join(words)
    except Exception as e:
        print(f"Error processing text: {text}")
        return text

def big_lot_predict(da_list: list[str])->list[int]:
    if len(da_list)==0:
        return []

    x_list=[]
    for i in da_list:
        processed_text = preprocess_text(i)
        x_list.append(processed_text)
    x = loaded_vector.transform(x_list)
    predictions = loaded_model.predict(x)
    return predictions


if __name__ == '__main__':
    rest = big_lot_predict(
        [
            """#互动抽奖#影石旗舰影像运动相机Ace Pro 2正式发布！
 AI双芯出动，画质更出众；4K60fps夜景录像，暗光画质「天花板」；全新一代徕卡SUMMARIT镜头，树立旗舰运动影像新标杆！
【关注@影石Insta360 】转发+评论此动态，11月22日抽送一台Ace Pro 2 （中奖规则见置顶评论）"""

        ]
    )
    print(rest)

