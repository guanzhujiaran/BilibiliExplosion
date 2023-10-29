import grpc
import requests

import bilibili.dynamic.interfaces.feed.v1.api_pb2 as dynamic_api
import bilibili.dynamic.interfaces.feed.v1.api_pb2_grpc as dynamic_grpc
import google.protobuf.text_format as text_format
import bilibili.dynamic.common.dynamic_pb2 as dynamic_resp
from bilibili.app.dynamic.v2.dynamic_pb2 import (DynAllReq,
    DynMixUpListViewMoreReq,
    DynSpaceReq,
    DynSpaceRsp,)

createdyn = dynamic_api.CreateDynReq(
    meta={},
    content={'contents': [{'raw_text': '1', 'type': 1, 'biz_id': ''}]},
    scene=4,
    repost_src={'dyn_id': 123456789, 'revs_id': {'dyn_type': 2, 'rid': 123456}},
    upload_id='14'
)
print(createdyn)
url = 'https://grpc.biliapi.net/bilibili.main.dynamic.feed.v1.Feed/CreateDyn'
headers = {
    'content-type': 'application/grpc',
    'accept-encoding': 'gzip',
    'user-agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0.1; oppo R11s Plus Build/V417IR) 6.89.0 os/android model/oppo R11s Plus mobi_app/android build/6890300 channel/html5_app_bili innerVer/6890310 osVer/6.0.1 network/2',
    'env': 'prod',
    'app-key': 'android64',
    'x-bili-device-bin': 'CAEQvMakAxolWFo3RUVGMjc5Qzg3Mjk0RDRFNDQ2REQ5QTFERTkwNzMxNEJBMyIHYW5kcm9pZCoHYW5kcm9pZDoOaHRtbDVfYXBwX2JpbGlCBE9QUE9KDm9wcG8gUjExcyBQbHVzUgU2LjAuMVpANmFhOWMwNDM3MzQ0NDU2MWQzYmRjODUyNjJmNzQ2NGQyMDIyMDQyMDE3NTMzOTkyNDhlZGJlYWViZDE5ZGFmNWJANmFhOWMwNDM3MzQ0NDU2MWQzYmRjODUyNjJmNzQ2NGQyMDIyMDQyMDE3NTMzOTkyNDhlZGJlYWViZDE5ZGFmNWoGNi44OS4wckA2YWE5YzA0MzczNDQ0NTYxZDNiZGM4NTI2MmY3NDY0ZDIwMjIwNDIwMTc1MzM5OTI0OGVkYmVhZWJkMTlkYWY1eKOw/5IG',
    'x-bili-metadata-bin': 'CiA1YzkxMGRhMGNjM2E5YTA1MzcyMzA3N2JlYjRkN2I5MRIHYW5kcm9pZCC8xqQDKg5odG1sNV9hcHBfYmlsaTIlWFo3RUVGMjc5Qzg3Mjk0RDRFNDQ2REQ5QTFERTkwNzMxNEJBMzoHYW5kcm9pZA',
    'authorization': 'identify_v1 5c910da0cc3a9a053723077beb4d7b91',
}

with grpc.aio.secure_channel('grpc.biliapi.net',grpc.ssl_channel_credentials()) as channel:
    res=1

