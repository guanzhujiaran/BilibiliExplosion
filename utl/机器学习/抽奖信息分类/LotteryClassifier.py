# -*- coding: utf-8 -*-
import os
import pickle
import random
import sys
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from CONFIG import CONFIG


class ML:
    def __init__(self):
        self.__rootDir = CONFIG.root_dir + 'utl/机器学习/抽奖信息分类/'
        if not os.path.exists(self.__rootDir + 'model'):
            os.mkdir(os.path.abspath(self.__rootDir + 'model'))
        if not os.path.exists(os.path.abspath(self.__rootDir + 'model/Vec_Lottery.pickle')):  # 向量模型
            self._Vec = self.Model_Vector_train(self._sentense_prepare())
        else:
            with open(self.__rootDir + 'model/Vec_Lottery.pickle', 'rb') as f:
                self._Vec = pickle.load(f)  # 将模型存储在变量clf_load中
        self.SVM = None  # SVM模型
        self.NB = None  # 贝叶斯模型

    def _text_repl(self, dynamic_conent):
        dynamic_conent = dynamic_conent.replace('null', '')
        dynamic_conent = dynamic_conent.replace('\\r\\n', '\n')
        dynamic_conent = dynamic_conent.replace('\\n', '\n')
        dynamic_conent = dynamic_conent.replace('\u200b', '')
        return dynamic_conent

    def _preprocess_text(self, content_lines, sentences, category):
        for line in content_lines:
            try:
                content = line.split('\t')[4]
                content = self._text_repl(content)
                sentences.append((content, category))
            except Exception as e:
                print(line)
                continue
        return sentences

    def Model_Vector_train(self, sentences: list[str]) -> CountVectorizer:
        random.shuffle(sentences)
        x, y = zip(*sentences)
        x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=114514)
        vec = CountVectorizer(
            analyzer='word',  # tokenise by character ngrams
            max_features=4000,  # keep the most common 4000 ngrams
        )
        vec.fit(x_train)
        return vec

    def _sentense_prepare(self) -> list[str]:
        sentences = []
        with open(self.__rootDir + 'data/抽奖/所有抽奖信息记录.csv', 'r', encoding='utf-8') as lottery:
            sentences.extend(self._preprocess_text(lottery.readlines(), sentences, '抽奖'))
        with open(self.__rootDir + 'data/非抽奖/所有无用信息.csv', 'r', encoding='utf-8') as nonlottery:
            sentences.extend(self._preprocess_text(nonlottery.readlines(), sentences, '非抽奖'))
        return sentences

    def _train_data_prepare(self, sentences: list[str]) -> tuple:
        random.shuffle(sentences)
        x, y = zip(*sentences)
        x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=114514, train_size=0.8)
        return x_train, x_test, y_train, y_test

    def _NB_Lottery_Classifier_train(self) -> MultinomialNB:
        sentences = self._sentense_prepare()
        x_train, x_test, y_train, y_test = self._train_data_prepare(sentences)
        classifier = MultinomialNB()  # 多项式分布的朴素贝叶斯
        classifier.fit(self._Vec.transform(x_train), y_train)
        res_score = classifier.score(self._Vec.transform(x_test), y_test)
        print('贝叶斯分数：', res_score)
        with open(self.__rootDir + 'model/NB_Lottery.pickle', 'wb') as f:
            pickle.dump(classifier, f)  # 将训练好的模型clf存储在变量f中，且保存到本地
        return classifier

    def _SVM_Lottery_Classifier_tarin(self) -> SVC:
        sentences = self._sentense_prepare()
        x_train, x_test, y_train, y_test = self._train_data_prepare(sentences)
        svm = SVC(probability=True)
        params = [
            {'kernel': ['linear'], 'C': [1, 10, 100]},
            {'kernel': ['poly'], 'C': [1, 10], 'degree': [2, 3]},
            {'kernel': ['rbf'], 'C': [1, 10, 100],
             'gamma': [1, 0.1, 0.01, 0.001]}]
        model = GridSearchCV(estimator=svm, param_grid=params, cv=5, n_jobs=-1)
        print('开始寻找SVM最优参数')
        model.fit(self._Vec.transform(x_train), y_train)
        print("SVM模型的最优参数：", model.best_params_)
        print("SVM最优模型分数：", model.best_score_)
        print("SVM最优模型对象：", model.best_estimator_)
        BestSVM = model.best_estimator_
        with open(self.__rootDir + 'model/SVM_Lottery.pickle', 'wb') as f:
            pickle.dump(BestSVM, f)  # 将训练好的模型clf存储在变量f中，且保存到本地
        return BestSVM

    def Lot_pred(self, Input_Content: str, model_name: str = 'svm') -> list[str]:
        if model_name.lower() == 'svm':
            if os.path.exists(self.__rootDir + 'model/SVM_Lottery.pickle'):
                with open(self.__rootDir + 'model/SVM_Lottery.pickle', 'rb') as f:
                    self.SVM = pickle.load(f)  # 将模型存储在变量clf_load中
            elif not self.SVM:
                self.SVM = self._SVM_Lottery_Classifier_tarin()

            model = self.SVM
        else:
            if os.path.exists(self.__rootDir + 'model/NB_Lottery.pickle'):
                with open(self.__rootDir + 'model/NB_Lottery.pickle', 'rb') as f:
                    self.NB = pickle.load(f)  # 将模型存储在变量clf_load中
            elif not self.NB:
                self.NB = self._NB_Lottery_Classifier_train()

            model = self.NB
        Input_Content = self._text_repl(Input_Content)

        pred = model.predict(self._Vec.transform([Input_Content]))
        return pred


if __name__ == '__main__':
    myclf = ML()
    dyc = '''
    互动抽奖  #2023高考季#
    #vivo S17系列#集结高校学长学姐为高考生加油！
    乾坤未定，你我皆黑马。
    愿你用落笔回应青春的汗水，用祝福坚定自己的内心。

    #vivo S17系列#人像，比肩旗舰。用S17 Pro专业长焦人像镜头，坚定姿态最青春。来评论区许愿，抽送vivo S17手机一台。
    '''
    res = myclf.Lot_pred(dyc, model_name='SVM')
    print(res)
