.PHONY: help all start start-excluding-fastapi stop restart restart-excluding-fastapi logs ps down clean

# 默认目标
help:
	@echo "可用命令:"
	@echo "  make help                     - 显示此帮助信息"
	@echo "  make all                      - 启动所有服务"
	@echo "  make start-excluding-fastapi  - 启动除 fastapi 以外的所有服务"
	@echo "  make start                    - 启动所有服务（等同于 make all）"
	@echo "  make stop                     - 停止所有服务"
	@echo "  make restart                  - 重启所有服务"
	@echo "  make restart-excluding-fastapi - 重启除 fastapi 以外的所有服务"
	@echo "  make logs [SERVICE]           - 查看日志（可指定服务名）"
	@echo "  make ps                       - 查看所有容器状态"
	@echo "  make down                     - 停止并删除所有容器"
	@echo "  make clean                    - 清理所有容器、网络和卷"

# 启动所有服务
all: start

start:
	docker-compose up -d

# 启动除 fastapi 以外的所有服务
start-excluding-fastapi:
	docker-compose up -d nginx goaccess standalone mysql redis rabbitmq unidbg postgres nodejs-pptr lm-studio casdoor rpa-browser

# 停止所有服务
stop:
	docker-compose stop

# 重启所有服务
restart:
	docker-compose restart

# 重启除 fastapi 以外的所有服务
restart-excluding-fastapi:
	docker-compose restart nginx goaccess standalone mysql redis rabbitmq unidbg postgres nodejs-pptr lm-studio casdoor rpa-browser

# 查看日志
logs:
	@if [ -z "$(SERVICE)" ]; then \
		docker-compose logs -f; \
	else \
		docker-compose logs -f $(SERVICE); \
	fi

# 查看容器状态
ps:
	docker-compose ps

# 停止并删除所有容器
down:
	docker-compose down

# 清理所有容器、网络和卷
clean:
	docker-compose down -v
	@echo "已清理所有容器、网络和卷"
