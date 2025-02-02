import asyncio

import Bilibili_methods.all_methods
from github.my_operator.get_others_lot.Tool.newSqlHelper.SqlHelper import SqlHelper
from github.my_operator.get_others_lot.new_main import OfficialLotType


async def main():
    s = SqlHelper
    BAPI = Bilibili_methods.all_methods.methods()
    alldynlist = await s.getAllDynInfo()

    for i in alldynlist:
        if i.officialLotType == OfficialLotType.抽奖动态的源动态.value:
            i.isLot = 1
        else:
            if BAPI.daily_choujiangxinxipanduan(i.dynContent):
                i.isLot = 0
            else:
                i.isLot = 1
        await s.addDynInfo(i)


if __name__ == '__main__':
    asyncio.run(main())
