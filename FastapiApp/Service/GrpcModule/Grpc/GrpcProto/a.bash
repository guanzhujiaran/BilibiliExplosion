#!/bin/bash
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Deleting existing .py files in $TARGET_DIR ..."
find "$TARGET_DIR" -name "*.py" -type f -delete

echo "Compiling .proto files..."
find "$TARGET_DIR" -name "*.proto" -type f | while read proto_file; do
    python -m grpc_tools.protoc \
    --proto_path="$TARGET_DIR" \
    --python_out="$TARGET_DIR" \
    --grpc_python_out="$TARGET_DIR" \
    "$proto_file"
done

echo "Done."