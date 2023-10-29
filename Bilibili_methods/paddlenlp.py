# -*- coding: utf-8 -*-
import re
import time

from paddlenlp import Taskflow
class my_paddlenlp:
    def __init__(self):
        self.__sentiment_analysis = Taskflow('sentiment_analysis')
        self.__dialogue = Taskflow('dialogue')
        self.__information_extraction = Taskflow('information_extraction',schema=[])

    def sentiment_analysis(self, input_Msg):
        '''
        正向返回True负向返回False
        :param input_Msg:
        :return: boolen
        '''
        input_Msg=self.msg_filter(input_Msg)
        res = self.__sentiment_analysis(input_Msg)
        if res[0]['label']=='positive':
            return True
        else:
            return False

    def msg_filter(self, input_Msg):
        input_Msg = input_Msg.replace('\n', '').replace('\r', '').replace('\\n', '').replace('\\r', '')
        input_Msg = re.sub('\[.*?]', '', input_Msg)
        return input_Msg

    def dialogue(self, input_Msg):
        '''
        对话可以输入list也可以是str
        :param input_Msg:
        :return:
        '''
        if type(input_Msg) == list:
            retlist = []
            for i in input_Msg:
                i = self.msg_filter(i)
                if len(i) >= 512:
                    i = i[0:510]
                try:
                    res = self.__dialogue([i])[0].replace(',', '，')
                except:
                    print(i)
                    print('Please check input value.')
                    res = 'None'
                retlist.append(res)
            return retlist
        else:
            input_Msg = self.msg_filter(input_Msg)
            res = self.__dialogue([input_Msg])[0].replace(',', '，')
            if res:
                return res
            else:
                return self.dialogue(input_Msg)

    def information_extraction(self,input_Msg,schema):
        input_Msg=self.msg_filter(input_Msg)
        if input_Msg!='':
            self.__information_extraction.set_schema(schema)
            res=self.__information_extraction(input_Msg)
            retdict={}
            for i in schema:
                if res[0].get(i):
                    retdict.update({i:res[0].get(i)[0].get('text')})
                else:
                    retdict.update({i:None})
            print(retdict)
        else:
            retdict = {}
            for i in schema:
                retdict.update({i: None})
        return retdict

    # def similar_meaning_rewrite(self):
    #     pass
    #
    #


