"""
开发环境
测试并开发api用！
"""
import uvicorn

if __name__=='__main__':
    uvicorn.run(app="router.main_route:app", host='127.0.0.1', port=3090, reload=True,
                log_level="warning")