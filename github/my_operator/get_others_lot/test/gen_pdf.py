import pandas as pd


df = pd.read_csv('../result/过滤抽奖信息.csv',index_col=None,sep='\t',)
df.to_html('result.html', index=False)
