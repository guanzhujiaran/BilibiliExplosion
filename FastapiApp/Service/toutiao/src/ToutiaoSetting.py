class TouTiaoDb:
    SpaceFeedDataDb = fr'sqlite:////ToutiaoDb/SpaceFeedData.db?check_same_thread=False'
    AIO_SpaceFeedDataDb = fr'sqlite+aiosqlite:////ToutiaoDb/SpaceFeedData.db?check_same_thread=False'


class CONFIG:
    DBSetting = TouTiaoDb()
    root_dir = "//"
