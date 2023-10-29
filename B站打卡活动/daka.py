import requests
import hashlib

# resource_id
# 6246d4801d608c34d3f3e293   'daka_id': 548046   'dingyue_id': 548078
# 6241cabc70134ba2f7702b9e   'daka_id': 531281   'dingyue_id': 531335
# 61b30d290a2a5567f8436145   'daka_id': 463852   'dingyue_id': 456131
# 622af5c18a1f6d704fb17e93
activity_id = '6241cabc70134ba2f7702b9e'
# 624564991d608c34d3f3e28e

# daka_id=531281
url = 'https://api.bilibili.com/x/activity/daka/activity_info?activity_id={}&csrf=154b5f52293d809f65c3705aacd71cb6'.format(
    activity_id)
req = requests.get(url)
print(req.json())
