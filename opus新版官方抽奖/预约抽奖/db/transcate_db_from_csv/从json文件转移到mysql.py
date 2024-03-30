import asyncio

import time
import ast
from opus新版官方抽奖.预约抽奖.db.sqlHelper import SqlHelper

async def main():
    ret_list = []
    with open('../../最后一次更新的直播预约.csv', 'r', encoding='utf-8') as f:
        for i in f.readlines():
            ret_list.append(ast.literal_eval(i))

    sql_helper = SqlHelper()
    nowRound = await sql_helper.get_latest_reserve_round()
    for idx, contents in enumerate(ret_list):
        await sql_helper.add_reserve_info_by_resp_dict(
            contents, nowRound.round_id
        )


if __name__ == '__main__':
    asyncio.run(main())
