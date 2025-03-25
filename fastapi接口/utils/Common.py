import asyncio

def ensure_asyncio_loop():
    if asyncio.get_event_loop():
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
