import json
import time

import redis
from loguru import logger

r = redis.Redis(host='localhost', port=11451, db=0)
def push_data_manually(da:dict,isanchor:bool=True):
    if isanchor:
        if not r.exists(da['server_data_id']):
            anchor_left_ts = int(da['time'] + da['current_ts'] - int(time.time()))
            logger.debug(f'添加至redis {da["server_data_id"]}')
            r.setex(da['server_data_id'], anchor_left_ts,
                    json.dumps(da)
                    )
    else:
        if not r.exists(da['lot_id']):
            popularity_red_pocket_left_ts = int(da['end_time'] - int(time.time()))
            logger.debug(f'添加至redis {da["lot_id"]}')
            r.setex(da['lot_id'],
                    popularity_red_pocket_left_ts if popularity_red_pocket_left_ts > 0 else 1,
                    json.dumps(da)
                    )

if __name__ == '__main__':
    lot_data = {}
    push_data_manually(
        lot_data,
        isanchor=True
    )
    