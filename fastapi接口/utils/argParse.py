import argparse


def parse():
    parser = argparse.ArgumentParser(
        prog='lot_fastapi',  # 程序名
        description='lottery info fastapi backend',  # 描述
    )
    parser.add_argument('-l', '--logger', type=int, default=0, choices=[0, 1])
    args = parser.parse_args()
    return args
