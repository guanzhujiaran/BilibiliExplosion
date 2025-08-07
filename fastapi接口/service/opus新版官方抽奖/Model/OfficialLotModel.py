from fastapi接口.service.grpc_module.src.SQLObject.models import ArticlePubRecord


class LotDetail:
    """
    抽奖信息详情
    """

    def __init__(self, lottery_id, dynamic_id, lottery_time, first_prize, second_prize,
                 third_prize, first_prize_cmt, second_prize_cmt, third_prize_cmt, participants, article_pub_record):
        self.lottery_id: int = lottery_id
        self.dynamic_id: str = dynamic_id
        self.lottery_time: int = lottery_time  # 时间戳
        self.first_prize: int = first_prize  # 一等奖人数
        self.second_prize: int = second_prize  # 二等奖人数
        self.third_prize: int = third_prize  # 三等奖人数
        self.first_prize_cmt: str = first_prize_cmt  # 奖品描述
        self.second_prize_cmt: str = second_prize_cmt
        self.third_prize_cmt: str = third_prize_cmt
        self.participants: int = participants  # 参加人数
        chance_number: int = 100 if int(participants) <= (
                int(first_prize) + int(second_prize) + int(third_prize)) else (
                                                                                      int(first_prize) + int(
                                                                                  second_prize) + int(
                                                                                  third_prize)) / int(
            participants) * 100
        self.chance: str = "%.2f%%" % chance_number
        self.article_pub_record: ArticlePubRecord | None = article_pub_record
