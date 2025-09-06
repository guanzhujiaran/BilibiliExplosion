import asyncio

from utl.代理.SealedRequests import my_async_httpx as my_req


url = 'https://tls.browserleaks.com/json'
url = 'https://6.ipw.cn'
result = asyncio.run(my_req.request(url=url, method='GET', headers=(
    (
        'User-Agent',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),),
                                    proxies={'http': 'http://127.0.0.1:63391',
                                             'https': 'http://127.0.0.1:63391'}
                                    ))
print(result.text)
