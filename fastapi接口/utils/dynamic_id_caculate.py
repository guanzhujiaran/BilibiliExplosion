def dynamic_id_2_ts(dynamic_id: int|str) -> int:
    """
    返回的是秒级时间戳
    :param dynamic_id:
    :return:
    """
    return int((int(dynamic_id) + 6437415932101782528) / 4294939971.297)


def ts_2_fake_dynamic_id(ts: int) -> int:
    """

    :param ts:秒级时间戳
    :return:
    """
    return int(ts * 4294939971.297 - 6437415932101782528)
