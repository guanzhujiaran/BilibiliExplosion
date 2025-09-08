module.exports = {
    apps: [{
        name: "fastapi_app",
        version: "1.14.514",
        script: "./main.py",
        interpreter: '.././venv/bin/python',
        env: {"LANG": "zh_CN.UTF-8"},
        args: "--logger 0", //是否开启fastapi的日志
        error_file: '/dev/null',
        out_file: '/dev/null',
    }
    ]
}
