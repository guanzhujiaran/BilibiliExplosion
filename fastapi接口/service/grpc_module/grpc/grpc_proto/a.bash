#!/bin/bash

find . -name "*.proto" -type f | while read proto_file; do
    # 使用 protoc 编译每个 .proto 文件
    python -m grpc_tools.protoc \
        --proto_path=. \
        --python_out=. \
        --grpc_python_out=. \
        "$proto_file"
done