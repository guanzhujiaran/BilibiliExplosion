class TouTiaoDb:
    SpaceFeedDataDb = fr'sqlite:///H:/ToutiaoDb/SpaceFeedData.db?check_same_thread=False'
    AIO_SpaceFeedDataDb = fr'sqlite+aiosqlite:///H:/ToutiaoDb/SpaceFeedData.db?check_same_thread=False'


class CONFIG:
    DBSetting = TouTiaoDb()
    root_dir = "//"
