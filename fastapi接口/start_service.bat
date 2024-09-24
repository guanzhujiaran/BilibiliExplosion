@echo off
cd K:\python test
K:
start  /B /realtime C:\ProgramData\miniconda3\envs\Bili310\python.exe fastapi接口/请求代理_ver_database_fastapi.py
start /B /realtime C:\ProgramData\miniconda3\envs\Bili310\python.exe fastapi接口/scripts/start_other_service.py

pause