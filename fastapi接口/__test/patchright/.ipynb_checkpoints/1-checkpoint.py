import asyncio

import aiomonitor
# patchright here!
from patchright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir='./user_data',
            headless=False,
        )
        page = await browser.new_page()
        await page.goto('http://playwright.dev')
        loop = asyncio.get_running_loop()
        run_forever = loop.create_future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass