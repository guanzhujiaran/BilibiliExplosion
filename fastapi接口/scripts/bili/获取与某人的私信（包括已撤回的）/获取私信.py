# noinspection PyUnresolvedReferences
import json

import Bilibili_methods.all_methods

mymethod = Bilibili_methods.all_methods.methods()

if __name__ == '__main__':
    msg_dict = dict()
    cookie = ""
    ua = ""
    uid = 1945493249
    msg_data = mymethod.get_all_sixin(uid, cookie, ua).get('data').get('messages')
    # print(msg_data)
    index = 1
    for i in msg_data:
        if i.get('msg_type') == 5:
            print(i)
            continue
        else:
            msg_dict.update({index: {i.get('sender_uid'): {'content': json.loads(i.get('content')).get('content'),
                                                           'timestamp': i.get('timestamp')}}})
            index += 1
    print(msg_dict)
