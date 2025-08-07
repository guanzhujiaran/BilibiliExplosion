import datetime


def str_2_DateTime(date_string: str, date_format: str = '%Y-%m-%dT%H:%M:%S', time_zone_offset=0) -> datetime.datetime:
    datetime_object = datetime.datetime.strptime(date_string, date_format) + datetime.timedelta(
        hours=time_zone_offset)
    return datetime_object


def ts_2_DateTime(timestamp: int | float, time_zone_offset=0) -> datetime.datetime:
    datetime_object = datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(
        hours=time_zone_offset)
    return datetime_object
