import pandas
from pandasgui import show

df = pandas.read_csv('../opus新版官方抽奖/预约抽奖/result/全部抽奖预约.csv',low_memory=False,dtype=str)
show(df)