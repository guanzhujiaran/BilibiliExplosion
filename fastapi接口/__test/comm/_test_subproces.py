import subprocess

# 不启用 text=True，应该返回 bytes
proc = subprocess.Popen(['echo', 'Hello World'], stdout=subprocess.PIPE)
output = proc.stdout.read()
print(type(output))  # 应该是 <class 'bytes'>