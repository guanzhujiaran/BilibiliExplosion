import jieba
import numpy as np
import os
from PIL import Image
from datetime import datetime
import pandas as pd
from collections import Counter
from wordcloud import WordCloud, ImageColorGenerator
import matplotlib.pyplot as plt

from CONFIG import CONFIG


def GenWordCloudBydf(df,date_start:datetime):
    # 将所有文本连接成一个长字符串
    path = CONFIG.root_dir + 'grpc获取动态/src/根据日期获取抽奖动态/'
    font_path = path + '花园明朝.ttf'
    back_img_path = path + 'favicon.ico'
    if not os.path.exists(path+'dataAnalysis'):
        os.mkdir(path+'dataAnalysis')
    if not os.path.exists(path+'dataAnalysis/WordCloud'):
        os.mkdir(path+'dataAnalysis/WordCloud')
    text = ' '.join(df['动态内容'].astype(str))
    save_csv_path = f'dataAnalysis/WordCloud/{date_start.year}/{date_start.month}/{date_start.year}_{date_start.month}_{date_start.day}_词频.csv'
    save_png_path = f'dataAnalysis/WordCloud/{date_start.year}/{date_start.month}/{date_start.year}_{date_start.month}_{date_start.day}_词云图.png'

    seg_list = jieba.cut(text, cut_all=False)
    words = ' '.join(seg_list)
    stopwords = set([line.strip() for line in open(path + 'chinese_stopwords.txt', 'r', encoding='utf-8')])
    filtered_words = [word for word in words.split() if word not in stopwords and len(word) > 1]

    # 显示词频统计的前10个单词
    if not os.path.exists(path + f'dataAnalysis/WordCloud/{date_start.year}/{date_start.month}'):
        os.makedirs(path + f'dataAnalysis/WordCloud/{date_start.year}/{date_start.month}')

    # 生成词云图

    backgroud_Image = plt.imread(back_img_path)
    img = Image.fromarray(backgroud_Image)
    img_resize = img.resize((1000, 700))
    plt.imshow(img)
    plt.show()
    plt.imshow(img_resize)
    plt.show()
    wordcloud = WordCloud(width=1080,
                          height=765,
                          background_color=None,
                          mode="RGBA",
                          contour_color='blue',
                          stopwords=stopwords,
                          min_font_size=10,
                          max_font_size=200,
                          random_state=42,
                          scale=2,
                          font_path=font_path,
                          mask=np.array(img_resize)
                          ).generate(' '.join(filtered_words))
    wordcloud.recolor(color_func=ImageColorGenerator(np.array(img_resize)))

    wordcloud.to_file(save_png_path)

    word_counts = Counter(filtered_words)
    word_freq_df = pd.DataFrame(word_counts.items(), columns=['word', 'frequency']).sort_values('frequency',
                                                                                                ascending=False)
    word_freq_df.head(100).to_csv(save_csv_path, index=False,encoding='utf-8')

if __name__ == '__main__':
    main_df = pd.read_csv(r'K:\python test\grpc获取动态\src\根据日期获取抽奖动态\result\2024\3\2024_3_13_抽奖信息.csv',sep='\t',encoding='utf-8')
    GenWordCloudBydf(main_df,datetime(2077,3,22,12,33,33))