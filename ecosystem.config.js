module.exports = {
    apps: [{
        name: "fastapi_app",
        version: "1.14.514",
        script: "./fastapi接口/请求代理_ver_database_fastapi.py",
        interpreter: 'python',
        env: {"LANG": "zh_CN.UTF-8"},
        args: "--logger 0", //是否开启fastapi的日志
    }]
}
