import os
from urllib.parse import urlencode
import subprocess
from functools import partial
subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
import execjs


class ToutiaoDecrypt:
    def __init__(self):
        _current_file_dir=os.path.dirname(os.path.abspath(__file__))
        _node_modules =  _current_file_dir+ '/node_modules'
        _a_bogus_js_raw = open(_current_file_dir + '/Toutiao_a_bogus.js', 'r',
                               encoding='utf-8').read()
        self._a_bogus_gen = execjs.compile(_a_bogus_js_raw, cwd=_node_modules)

    def gen_abogus(self, params, ua) -> str:
        a_bogus = self._a_bogus_gen.call('get_a_bogus', urlencode(params), ua)
        return a_bogus


if __name__ == '__main__':
    ___ = ToutiaoDecrypt()
    ab = ___.gen_abogus({"114": "514"}, '11514:1919810')
    print(ab)
