import asyncio
import os
import random
from math import sqrt

from patchright.async_api import async_playwright


class PlaywrightOperator:
    def __init__(self, user_data_dir: str, headless=False):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.user_data_dir = current_dir / 'user_data' / user_data_dir
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.mouse_x = 0
        self.mouse_y = 0

    async def launch(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless
        )
        self.page = self.browser.pages[0]
        self.mouse_x = 0
        self.mouse_y = 0

    async def goto(self, url):
        """访问网页"""
        return await self.page.goto(url)

    def random_point_in_box(self, box, padding=5):
        """
        在元素的 bounding_box 内部生成一个随机坐标点
        :param box: 元素的 bounding_box
        :param padding: 边距，防止点到边缘
        :return: (x, y) 随机坐标
        """
        x_min = box['x'] + padding
        x_max = box['x'] + box['width'] - padding
        y_min = box['y'] + padding
        y_max = box['y'] + box['height'] - padding

        if x_max <= x_min or y_max <= y_min:
            raise ValueError("元素太小，无法生成有效的点击点")

        x = random.uniform(x_min, x_max)
        y = random.uniform(y_min, y_max)
        return x, y

    async def move_mouse_to(self, x, y, steps=10, smooth=True):
        """
        自定义自然鼠标移动路径
        :param x: 目标 x 坐标
        :param y: 目标 y 坐标
        :param steps: 移动步数
        :param smooth: 是否根据距离调整步数
        """
        dx = x - self.mouse_x
        dy = y - self.mouse_y
        distance = sqrt(dx ** 2 + dy ** 2)

        if smooth:
            steps = max(steps, int(distance // 5))

        for i in range(1, steps + 1):
            progress = i / steps
            nx = self.mouse_x + dx * progress + random.uniform(-3, 3)
            ny = self.mouse_y + dy * progress + random.uniform(-3, 3)
            await self.page.mouse.move(nx, ny)
            self.mouse_x, self.mouse_y = nx, ny
            await asyncio.sleep(random.uniform(0.02, 0.08))

    async def click(self, selector, natural_move=True):
        """点击元素，带自然移动和安全坐标偏移"""
        box = await self.page.locator(selector).bounding_box()
        if not box:
            raise Exception(f"Element {selector} not found")

        # 获取一个落在元素内部的安全坐标
        target_x, target_y = self.random_point_in_box(box, padding=10)

        if natural_move:
            await self.move_mouse_to(target_x, target_y)
        else:
            await self.page.mouse.move(target_x, target_y)

        await self.random_delay(0.2, 0.5)
        await self.page.mouse.click(target_x, target_y)

    async def hover(self, selector, natural_move=True):
        """悬停元素，带自然移动和安全坐标偏移"""
        box = await self.page.locator(selector).bounding_box()
        if not box:
            raise Exception(f"Element {selector} not found")

        target_x, target_y = self.random_point_in_box(box, padding=5)

        if natural_move:
            await self.move_mouse_to(target_x, target_y)
        else:
            await self.page.mouse.move(target_x, target_y)

    async def type_text(self, selector, text, natural_move=True):
        """输入文本，模拟人类打字速度，并可选自然移动到输入框"""
        box = await self.page.locator(selector).bounding_box()
        if not box:
            raise Exception(f"Element {selector} not found")

        target_x, target_y = self.random_point_in_box(box, padding=5)

        if natural_move:
            await self.move_mouse_to(target_x, target_y)

        await self.random_delay(0.5, 1.0)
        await self.page.fill(selector, "")
        for char in text:
            await self.page.type(selector, char)
            await self.random_delay(0.05, 0.2)

    async def drag_and_drop(self, source_selector, target_selector, natural_move=True):
        """拖拽操作，支持自然移动到起点和终点，并限制在元素范围内"""
        source_box = await self.page.locator(source_selector).bounding_box()
        target_box = await self.page.locator(target_selector).bounding_box()

        if not source_box or not target_box:
            raise Exception("无法获取元素边界框")

        src_target = self.random_point_in_box(source_box, padding=5)
        tgt_target = self.random_point_in_box(target_box, padding=5)

        if natural_move:
            await self.move_mouse_to(*src_target)
        await self.page.mouse.down()
        await asyncio.sleep(0.2)
        if natural_move:
            await self.move_mouse_to(*tgt_target)
        await self.page.mouse.up()

    async def scroll_to_bottom(self):
        """滚动到底部"""
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def random_delay(self, min_delay=0.5, max_delay=1.5):
        """随机延迟"""
        await asyncio.sleep(random.uniform(min_delay, max_delay))

    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def anti_detect(self):
        """防检测脚本"""
        await self.page.add_init_script("""
        delete navigator.__proto__.webdriver;
        window.chrome = {runtime: {}};
        """)
