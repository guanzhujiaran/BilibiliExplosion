class Singleton:

    """
    单例类装饰器，可以用于想实现单例的任何类。注意，不能用于多线程环境。
    使用方式
    # 装饰器
    @Singleton
    class A:
        def __init__(self):
            pass

        def display(self):
            return id(self)

    if __name__ == '__main__':
        s1 = A.Instance()
        s2 = A.Instance()
        print(s1, s1.display())
        print(s2, s2.display())
        print(s1 is s2)

    """

    def __init__(self, cls):
        """ 需要的参数是一个类 """
        self._cls = cls

    def Instance(self):
        """
        返回真正的实例
        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._cls()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)