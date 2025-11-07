FROM lmstudio/llmster-preview:cpu

# 复制并启用自定义入口脚本
COPY init.sh /init.sh
RUN chmod +x /init.sh

# 覆盖 ENTRYPOINT
ENTRYPOINT ["/init.sh"]