import asyncio
import json
import time

import websockets


async def client(send_dm_data_list):
    async with websockets.connect("ws://localhost:5705") as websocket:
        while 1:
            for i in send_dm_data_list:
                await websocket.send(json.dumps(i))
                response = await websocket.recv()
                print("Received:", response)
                time.sleep(0.3)

if __name__ == "__main__":
    send_dm_data_list=[
        {
            "room_id": 24354075,
            "dm_msg": '1',
            "cheat_mode": False,
            "stop_flag": False,
            "send_ts": int(time.time())  # (number) 请求发送弹幕的时间戳 xx秒
        },
    ]
    asyncio.get_event_loop().run_until_complete(client(send_dm_data_list))
