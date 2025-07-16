import asyncio
import os
import random
import typing
from math import sqrt

from patchright.async_api import async_playwright, Browser, Page, Playwright
from patchright.async_api._generated import Response


class PlaywrightOperator:
    def __init__(self, user_data_dir: str, *, headless=False):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.user_data_dir = os.path.join(current_dir, 'user_data', user_data_dir)
        print(f'用户数据目录: {self.user_data_dir}')
        self.headless = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context = None
        self.page: Page | None = None
        self.mouse_x = 0
        self.mouse_y = 0
        self._lock = asyncio.Lock()

    async def _ensure_page_ready(self):
        """确保页面处于可操作状态"""
        if not self.page or self.page.is_closed():
            await self.launch()
            if not self.page or self.page.is_closed():
                raise RuntimeError("无法恢复页面，页面仍处于关闭状态")

    async def launch(self):
        """启动浏览器"""
        async with self._lock:
            if self.browser and self.browser.is_connected():
                return
            if self.playwright:
                await self.playwright.stop()
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless
            )
            pages = self.browser.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.browser.new_page()
            self.mouse_x = 0
            self.mouse_y = 0

    async def goto(self, url):
        async with self._lock:
            await self._ensure_page_ready()
            result = await self.page.goto(url)
            await self.__random_delay(1.0, 2.5)  # 页面加载后等待
            return result

    async def click(self, selector, natural_move=True):
        async with self._lock:
            await self._ensure_page_ready()
            box = await self.page.locator(selector).bounding_box()
            if not box:
                raise Exception(f"Element {selector} not found")
            target_x, target_y = self.__random_point_in_box(box, padding=10)

            if natural_move:
                await self.__move_mouse_to(target_x, target_y)
            else:
                await self.page.mouse.move(target_x, target_y)

            await self.__random_delay(0.2, 0.5)
            await self.page.mouse.click(target_x, target_y)
            await self.__random_delay(0.5, 1.5)  # 点击后等待反应时间

    async def hover(self, selector, natural_move=True):
        async with self._lock:
            await self._ensure_page_ready()
            box = await self.page.locator(selector).bounding_box()
            if not box:
                raise Exception(f"Element {selector} not found")
            target_x, target_y = self.__random_point_in_box(box, padding=5)

            if natural_move:
                await self.__move_mouse_to(target_x, target_y)
            else:
                await self.page.mouse.move(target_x, target_y)

    async def type_text(self, selector, text, natural_move=True):
        async with self._lock:
            await self._ensure_page_ready()
            box = await self.page.locator(selector).bounding_box()
            if not box:
                raise Exception(f"Element {selector} not found")
            target_x, target_y = self.__random_point_in_box(box, padding=5)

            if natural_move:
                await self.__move_mouse_to(target_x, target_y)

            await self.__random_delay(0.5, 1.0)
            await self.page.fill(selector, "")
            for char in text:
                await self.page.type(selector, char)
                await self.__random_delay(0.05, 0.2)

    async def drag_and_drop(self, source_selector, target_selector, natural_move=True):
        async with self._lock:
            await self._ensure_page_ready()
            source_box = await self.page.locator(source_selector).bounding_box()
            target_box = await self.page.locator(target_selector).bounding_box()

            if not source_box or not target_box:
                raise Exception("无法获取元素边界框")

            src_target = self.__random_point_in_box(source_box, padding=5)
            tgt_target = self.__random_point_in_box(target_box, padding=5)

            if natural_move:
                await self.__move_mouse_to(*src_target)
            await self.page.mouse.down()
            await asyncio.sleep(0.2)
            if natural_move:
                await self.__move_mouse_to(*tgt_target)
            await self.page.mouse.up()

    async def scroll_to_bottom(self):
        async with self._lock:
            await self._ensure_page_ready()
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def close(self):
        async with self._lock:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

    def __random_point_in_box(self, box, padding=5):
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

    async def __move_mouse_to(self, x, y, steps=10, smooth=True):
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

    async def __random_delay(self, min_delay=0.5, max_delay=1.5):
        """随机延迟"""
        await asyncio.sleep(random.uniform(min_delay, max_delay))

    async def wait_for_url(self, url: typing.Union[str, typing.Pattern[str], typing.Callable[[str], bool]],
                           timeout: float = 30000):
        """等待页面跳转到指定 URL"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.wait_for_url(url, timeout=timeout)

    async def expect_response(self, url_or_predicate: typing.Union[
        str, typing.Pattern[str], typing.Callable[["Response"], bool]
    ],
                              *,
                              timeout: typing.Optional[float] = None, ):
        await self._ensure_page_ready()
        return self.page.expect_response(url_or_predicate, timeout=timeout)

    async def wait_for_load_state(self, load_state: str = "load", timeout: float = 30000):
        """等待页面加载状态完成，例如 'load', 'domcontentloaded', 'networkidle'"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.wait_for_load_state(state=load_state, timeout=timeout)

    async def reload(self, timeout: float = 30000):
        """重新加载页面"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.reload(timeout=timeout)

    async def wait_for_event(self, event: str, timeout: float = 30000):
        """等待页面触发某个事件，比如 'popup', 'download'"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.wait_for_event(event, timeout=timeout)

    async def go_back(self, timeout: float = 30000):
        """返回上一页"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.go_back(timeout=timeout)

    async def go_forward(self, timeout: float = 30000):
        """前进到下一页"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.go_forward(timeout=timeout)

    async def bring_to_front(self):
        """将页面带到前台"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.bring_to_front()

    async def dblclick(self, selector: str, natural_move=True):
        """双击元素"""
        async with self._lock:
            await self._ensure_page_ready()
            box = await self.page.locator(selector).bounding_box()
            if not box:
                raise Exception(f"Element {selector} not found")
            target_x, target_y = self.__random_point_in_box(box, padding=5)
            if natural_move:
                await self.__move_mouse_to(target_x, target_y)
            else:
                await self.page.mouse.move(target_x, target_y)
            await self.page.mouse.dblclick(target_x, target_y)

    async def tap(self, selector: str):
        """触摸点击（用于移动端）"""
        async with self._lock:
            await self._ensure_page_ready()
            box = await self.page.locator(selector).bounding_box()
            if not box:
                raise Exception(f"Element {selector} not found")
            target_x, target_y = self.__random_point_in_box(box, padding=5)
            await self.page.tap(selector)

    async def fill(self, selector: str, value: str):
        """填写表单字段"""
        async with self._lock:
            await self._ensure_page_ready()
            await self.page.fill(selector, value)

    async def locator(self, selector: str):
        """获取元素定位器"""
        async with self._lock:
            await self._ensure_page_ready()
            return self.page.locator(selector)

    async def focus(self, selector: str):
        """聚焦到指定元素"""
        async with self._lock:
            await self._ensure_page_ready()
            await self.page.focus(selector)

    async def text_content(self, selector: str) -> str:
        """获取元素的文本内容"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.text_content(selector)

    async def inner_text(self, selector: str) -> str:
        """获取元素内部文本"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.inner_text(selector)

    async def inner_html(self, selector: str) -> str:
        """获取元素内部 HTML 内容"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.inner_html(selector)

    async def get_attribute(self, selector: str, attribute: str) -> str:
        """获取元素的某个属性值"""
        async with self._lock:
            await self._ensure_page_ready()
            return await self.page.get_attribute(selector, attribute)


if __name__ == '__main__':
    print(__file__)
