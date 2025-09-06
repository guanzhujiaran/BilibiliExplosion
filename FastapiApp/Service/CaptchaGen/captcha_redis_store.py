from Utils.redisTool.RedisManager import RedisManagerBase


class RedisHelper(RedisManagerBase):
    class RedisMap(RedisManagerBase.RedisMap):
        captcha_id = 'captcha:id:{id}'

    async def get_captcha(self, _id: str) -> str:
        if result := await self._get(self.RedisMap.captcha_id.format(id=_id)):
            return result
        else:
            return ''

    async def set_id(self, _id: str, value: str, _timeout: int = 600):
        """
        _id: id字符串，uuid直接生成就行
        value: 验证码
        """
        await self._setex(self.RedisMap.captcha_id.format(id=_id), value, _timeout)

    async def rm_id(self, _id):
        await self._del(self.RedisMap.captcha_id.format(id=_id))
