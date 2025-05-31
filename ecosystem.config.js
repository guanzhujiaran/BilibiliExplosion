module.exports = {
    apps: [{
        name: "fastapi_app",
        version: "1.14.514",
        script: "./fastapi接口/请求代理_ver_database_fastapi.py",
        interpreter: '/home/minato_aqua/BilibiliExplosion/py310/bin/python',
        env: {"LANG": "zh_CN.UTF-8"},
        args: "--logger 0", //是否开启fastapi的日志
    },
    {
        name: "faststream_app",
        version: "1.919.810",
        script: "./fastapi接口/faststream_app.py",
        interpreter: '/home/minato_aqua/BilibiliExplosion/py310/bin/python',
        env: {"LANG": "zh_CN.UTF-8"},
    }
    ]
}
