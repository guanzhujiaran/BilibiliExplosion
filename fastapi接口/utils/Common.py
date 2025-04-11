import asyncio

GLOBAL_SEM = asyncio.Semaphore(300)  # windows只能500来个selector，要更高的并发需要迁移到linux


def ensure_asyncio_loop():
    if asyncio.get_event_loop():
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
